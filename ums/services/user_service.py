"""
User Service for User Management Services (UMS)

This service handles the complete user journey:
- Anonymous user creation and management
- User recognition (fingerprint/session-based)
- User conversion (anonymous -> registered)
- Authentication and authorization
"""

from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt
import jwt
from fastapi import HTTPException, status

from ..models.user import User, UserSession, UserFingerprint, UserType, UserJourneyStage
from ..schemas.user_schemas import (
    UserCreate, UserLogin, UserConvert, SessionCreate,
    UserResponse, UserWithSessionResponse, AuthResponse,
    SessionResponse, FingerprintResponse
)
from .session_service import SessionService
from ..utils.session import generate_session_token
from ..utils.fingerprint import generate_fingerprint


class UserService:
    """Service for managing the complete user lifecycle"""

    def __init__(self, db: Session, secret_key: str = "your-secret-key"):
        self.db = db
        self.secret_key = secret_key
        self.session_service = SessionService(db)

    def create_anonymous_user(
        self,
        session_data: SessionCreate,
        request_ip: Optional[str] = None,
        request_user_agent: Optional[str] = None
    ) -> UserWithSessionResponse:
        """
        Create a new anonymous user with session tracking

        Args:
            session_data: Session creation data
            request_ip: Client IP address
            request_user_agent: Client user agent

        Returns:
            UserWithSessionResponse with user, session, and recognition info
        """
        # Check if user already exists by fingerprint
        existing_result = None
        if session_data.fingerprint:
            existing_result = self.session_service.find_existing_user_by_fingerprint(
                session_data.fingerprint
            )

        if existing_result:
            user, fingerprint = existing_result
            # Create new session for returning user
            session = self.session_service.create_session(user, session_data, request_ip, request_user_agent)

            return UserWithSessionResponse(
                user=UserResponse.from_orm(user),
                session=SessionResponse.from_orm(session),
                fingerprint=FingerprintResponse.from_orm(fingerprint) if fingerprint else None,
                is_returning=True,
                recognition_method="fingerprint"
            )

        # Create new anonymous user
        user, session, is_returning = self.session_service.get_or_create_user_session(
            session_data, request_ip, request_user_agent
        )

        return UserWithSessionResponse(
            user=UserResponse.from_orm(user),
            session=SessionResponse.from_orm(session),
            is_returning=is_returning,
            recognition_method="new"
        )

    def authenticate_by_session(self, session_token: str) -> Optional[UserWithSessionResponse]:
        """
        Authenticate user by session token

        Args:
            session_token: Session token to validate

        Returns:
            UserWithSessionResponse if valid session, None otherwise
        """
        result = self.session_service.find_existing_user_by_session(session_token)
        if not result:
            return None

        user, session = result

        # Get user's fingerprints for response
        fingerprints = self.db.query(UserFingerprint).filter(
            UserFingerprint.user_id == user.id
        ).all()

        latest_fingerprint = fingerprints[0] if fingerprints else None

        return UserWithSessionResponse(
            user=UserResponse.from_orm(user),
            session=SessionResponse.from_orm(session),
            fingerprint=FingerprintResponse.from_orm(latest_fingerprint) if latest_fingerprint else None,
            is_returning=user.user_type != UserType.ANONYMOUS,
            recognition_method="session"
        )

    def register_user(self, user_data: UserCreate) -> AuthResponse:
        """
        Register a new user (from anonymous or new)

        Args:
            user_data: User registration data

        Returns:
            AuthResponse with access token and user info
        """
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = self._hash_password(user_data.password)

        # Create new registered user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            name=user_data.name,
            user_type=UserType.REGISTERED,
            journey_stage=UserJourneyStage.CONVERTED,
            is_anonymous=False
        )

        self.db.add(user)
        self.db.flush()

        # Create session if session info provided
        session = None
        if user_data.session_info:
            session = self.session_service.create_session(user, user_data.session_info)
        else:
            # Create basic session
            session_data = SessionCreate()
            session = self.session_service.create_session(user, session_data)

        self.db.commit()

        # Generate access token
        access_token = self._generate_access_token(user.id)

        return AuthResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user),
            session=SessionResponse.from_orm(session)
        )

    def login_user(self, login_data: UserLogin) -> AuthResponse:
        """
        Login existing registered user

        Args:
            login_data: Login credentials and session info

        Returns:
            AuthResponse with access token and user info
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user or not self._verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Update last seen
        user.update_last_seen()

        # Create new session
        session_data = login_data.session_info or SessionCreate()
        session = self.session_service.create_session(user, session_data)

        self.db.commit()

        # Generate access token
        access_token = self._generate_access_token(user.id)

        return AuthResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user),
            session=SessionResponse.from_orm(session),
            is_returning=True
        )

    def convert_anonymous_to_registered(
        self,
        user_id: str,
        convert_data: UserConvert
    ) -> AuthResponse:
        """
        Convert anonymous user to registered user

        Args:
            user_id: ID of anonymous user to convert
            convert_data: Registration data

        Returns:
            AuthResponse with access token and updated user info
        """
        # Find anonymous user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.user_type == UserType.REGISTERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already registered"
            )

        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == convert_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password and update user
        hashed_password = self._hash_password(convert_data.password)
        user.promote_to_registered(convert_data.email, hashed_password, convert_data.name)

        # Get current active session
        active_sessions = self.session_service.get_user_sessions(user_id, active_only=True)
        session = active_sessions[0] if active_sessions else None

        self.db.commit()

        # Generate access token
        access_token = self._generate_access_token(user.id)

        return AuthResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user),
            session=SessionResponse.from_orm(session) if session else None,
            is_returning=True
        )

    def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Get user from JWT token

        Args:
            token: JWT access token

        Returns:
            User object if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("user_id")

            if user_id:
                return self.db.query(User).filter(User.id == user_id).first()
        except jwt.InvalidTokenError:
            pass

        return None

    def logout_user(self, session_token: str) -> bool:
        """
        Logout user by invalidating session

        Args:
            session_token: Session token to invalidate

        Returns:
            True if session was invalidated, False if not found
        """
        return self.session_service.invalidate_session(session_token)

    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with user analytics and journey data
        """
        analytics = self.session_service.get_user_analytics(user_id)

        # Add UMS-specific analytics
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            analytics.update({
                'conversion_funnel': {
                    'is_anonymous': user.user_type == UserType.ANONYMOUS,
                    'is_returning': user.user_type == UserType.RETURNING,
                    'is_registered': user.user_type == UserType.REGISTERED,
                    'conversion_potential': self._calculate_conversion_potential(user)
                },
                'engagement_insights': {
                    'session_frequency': analytics.get('total_sessions', 0) / max(analytics.get('days_since_first_visit', 1), 1),
                    'engagement_trend': self._get_engagement_trend(user)
                }
            })

        return analytics

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def _generate_access_token(self, user_id: str) -> str:
        """Generate JWT access token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7)  # 7 days expiry
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _calculate_conversion_potential(self, user: User) -> int:
        """Calculate user's potential for conversion (0-100)"""
        score = 0

        # Base score for engagement
        score += min(user.engagement_score // 10, 30)

        # Session count bonus
        score += min(user.total_sessions * 5, 25)

        # Message count bonus
        score += min(user.total_messages * 2, 20)

        # Time on platform bonus
        days_active = (datetime.utcnow() - user.first_visit_at).days
        score += min(days_active * 2, 25)

        return min(score, 100)

    def _get_engagement_trend(self, user: User) -> str:
        """Get user's engagement trend"""
        recent_sessions = self.session_service.get_user_sessions(user.id, active_only=False)

        if len(recent_sessions) < 2:
            return "insufficient_data"

        # Simple trend analysis based on recent session activity
        recent_activity = sum(1 for s in recent_sessions[:5] if s.messages_sent > 0)
        total_recent = min(len(recent_sessions), 5)

        activity_ratio = recent_activity / total_recent if total_recent > 0 else 0

        if activity_ratio >= 0.8:
            return "highly_engaged"
        elif activity_ratio >= 0.5:
            return "moderately_engaged"
        elif activity_ratio >= 0.2:
            return "low_engagement"
        else:
            return "at_risk"