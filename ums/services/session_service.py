"""
Session Service for User Management Services (UMS)

This service handles session management, browser fingerprinting,
and user recognition for anonymous and returning users.
"""

from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.user import User, UserSession, UserFingerprint, UserType
from ..schemas.user_schemas import SessionCreate, FingerprintCreate
from ..utils.fingerprint import (
    generate_fingerprint,
    extract_device_info,
    calculate_fingerprint_strength
)
from ..utils.session import (
    generate_session_token,
    calculate_session_expiry,
    parse_user_agent,
    extract_ip_info
)


class SessionService:
    """Service for managing user sessions and browser fingerprinting"""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user: User,
        session_data: SessionCreate,
        request_ip: Optional[str] = None,
        request_user_agent: Optional[str] = None
    ) -> UserSession:
        """
        Create a new user session with optional fingerprinting

        Args:
            user: User object
            session_data: Session creation data
            request_ip: Client IP address
            request_user_agent: Client user agent

        Returns:
            Created UserSession object
        """
        # Generate session token
        session_token = generate_session_token()

        # Use provided data or extract from request
        ip_address = session_data.ip_address or request_ip
        user_agent = session_data.user_agent or request_user_agent

        # Parse device information
        device_info = {}
        if user_agent:
            device_info = parse_user_agent(user_agent)

        if ip_address:
            device_info.update(extract_ip_info(ip_address))

        # Add any additional device info
        if session_data.device_info:
            device_info.update(session_data.device_info)

        # Create fingerprint if provided
        fingerprint_hash = None
        if session_data.fingerprint:
            fingerprint_hash = self._create_or_update_fingerprint(
                user, session_data.fingerprint
            )

        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            fingerprint_hash=fingerprint_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            expires_at=calculate_session_expiry(24)  # 24 hours
        )

        self.db.add(session)

        # Update user's session count and last seen
        user.total_sessions += 1
        user.update_last_seen()

        self.db.commit()
        self.db.refresh(session)

        return session

    def find_existing_user_by_fingerprint(
        self,
        fingerprint_data: FingerprintCreate
    ) -> Optional[Tuple[User, UserFingerprint]]:
        """
        Find an existing user by browser fingerprint

        Args:
            fingerprint_data: Fingerprint data to match

        Returns:
            Tuple of (User, UserFingerprint) if found, None otherwise
        """
        if not fingerprint_data.components:
            return None

        # Generate fingerprint hash
        fingerprint_hash = generate_fingerprint(fingerprint_data.components)

        # Look for existing fingerprint
        existing_fingerprint = self.db.query(UserFingerprint).filter(
            UserFingerprint.fingerprint_hash == fingerprint_hash
        ).first()

        if existing_fingerprint:
            # Update fingerprint usage
            existing_fingerprint.update_seen()
            existing_fingerprint.calculate_confidence()

            # Get the user
            user = self.db.query(User).filter(
                User.id == existing_fingerprint.user_id
            ).first()

            if user:
                # Promote anonymous user to returning if needed
                if user.user_type == UserType.ANONYMOUS:
                    user.promote_to_returning()

                self.db.commit()
                return user, existing_fingerprint

        return None

    def find_existing_user_by_session(
        self,
        session_token: str
    ) -> Optional[Tuple[User, UserSession]]:
        """
        Find an existing user by valid session token

        Args:
            session_token: Session token to validate

        Returns:
            Tuple of (User, UserSession) if found and valid, None otherwise
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()

        if session:
            # Check if session is expired
            if session.expires_at and datetime.utcnow() > session.expires_at:
                session.is_active = False
                self.db.commit()
                return None

            # Update session activity
            session.update_activity()

            # Get the user
            user = self.db.query(User).filter(
                User.id == session.user_id
            ).first()

            if user:
                user.update_last_seen()
                self.db.commit()
                return user, session

        return None

    def get_or_create_user_session(
        self,
        session_data: SessionCreate,
        request_ip: Optional[str] = None,
        request_user_agent: Optional[str] = None
    ) -> Tuple[User, UserSession, bool]:
        """
        Get existing user or create new one with session

        Args:
            session_data: Session creation data
            request_ip: Client IP address
            request_user_agent: Client user agent

        Returns:
            Tuple of (User, UserSession, is_returning_user)
        """
        is_returning = False
        user = None
        existing_session = None

        # First, try to find by fingerprint
        if session_data.fingerprint:
            result = self.find_existing_user_by_fingerprint(session_data.fingerprint)
            if result:
                user, fingerprint = result
                is_returning = True

        # If not found by fingerprint, create new anonymous user
        if not user:
            user = User(
                user_type=UserType.ANONYMOUS,
                is_anonymous=True
            )
            self.db.add(user)
            self.db.flush()  # Get user ID without committing

        # Create new session
        session = self.create_session(user, session_data, request_ip, request_user_agent)

        return user, session, is_returning

    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a user session

        Args:
            session_token: Session token to invalidate

        Returns:
            True if session was invalidated, False if not found
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()

        if session:
            session.is_active = False
            session.calculate_duration()
            self.db.commit()
            return True

        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=48)  # Clean up sessions older than 48 hours

        expired_sessions = self.db.query(UserSession).filter(
            UserSession.last_activity_at < cutoff_time,
            UserSession.is_active == True
        ).all()

        count = len(expired_sessions)

        for session in expired_sessions:
            session.is_active = False
            session.calculate_duration()

        self.db.commit()
        return count

    def get_user_sessions(self, user_id: str, active_only: bool = True) -> list[UserSession]:
        """
        Get all sessions for a user

        Args:
            user_id: User ID
            active_only: Return only active sessions

        Returns:
            List of UserSession objects
        """
        query = self.db.query(UserSession).filter(UserSession.user_id == user_id)

        if active_only:
            query = query.filter(UserSession.is_active == True)

        return query.order_by(UserSession.last_activity_at.desc()).all()

    def _create_or_update_fingerprint(
        self,
        user: User,
        fingerprint_data: FingerprintCreate
    ) -> str:
        """
        Create or update user fingerprint

        Args:
            user: User object
            fingerprint_data: Fingerprint data

        Returns:
            Fingerprint hash
        """
        if not fingerprint_data.components:
            return None

        # Generate fingerprint hash
        fingerprint_hash = generate_fingerprint(fingerprint_data.components)

        # Check if fingerprint already exists for this user
        existing = self.db.query(UserFingerprint).filter(
            UserFingerprint.user_id == user.id,
            UserFingerprint.fingerprint_hash == fingerprint_hash
        ).first()

        if existing:
            existing.update_seen()
            existing.calculate_confidence()
            return fingerprint_hash

        # Extract device info
        device_info = extract_device_info(fingerprint_data.components)

        # Calculate fingerprint strength
        strength = calculate_fingerprint_strength(fingerprint_data.components)

        # Create new fingerprint
        fingerprint = UserFingerprint(
            user_id=user.id,
            fingerprint_hash=fingerprint_hash,
            raw_fingerprint=fingerprint_data.components,
            browser_name=device_info.get('browser', 'Unknown'),
            os_name=device_info.get('os', 'Unknown'),
            device_type=device_info.get('device_type', 'Unknown'),
            screen_resolution=device_info.get('screen_resolution'),
            timezone=device_info.get('timezone'),
            language=device_info.get('language'),
            components_count=len(fingerprint_data.components),
            confidence_score=strength
        )

        self.db.add(fingerprint)
        return fingerprint_hash

    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with user analytics
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        sessions = self.get_user_sessions(user_id, active_only=False)
        fingerprints = self.db.query(UserFingerprint).filter(
            UserFingerprint.user_id == user_id
        ).all()

        total_session_time = sum(s.session_duration for s in sessions)
        avg_session_time = total_session_time / len(sessions) if sessions else 0

        return {
            'user_id': user_id,
            'user_type': user.user_type,
            'journey_stage': user.journey_stage,
            'total_sessions': len(sessions),
            'total_messages': user.total_messages,
            'engagement_score': user.engagement_score,
            'total_session_time': total_session_time,
            'avg_session_time': avg_session_time,
            'fingerprint_count': len(fingerprints),
            'first_visit': user.first_visit_at,
            'last_seen': user.last_seen_at,
            'days_since_first_visit': (datetime.utcnow() - user.first_visit_at).days
        }