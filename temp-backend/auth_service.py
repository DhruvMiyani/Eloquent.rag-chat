"""
Enhanced Authentication Service with Anonymous and Returning User Support
"""

import os
import jwt
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "eloquent-ai-secret-key-for-development-only-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days
ANONYMOUS_TOKEN_EXPIRE_DAYS = int(os.getenv("ANONYMOUS_TOKEN_EXPIRE_DAYS", "90"))  # 90 days

class AuthService:
    """Enhanced authentication service with anonymous and returning user support."""

    def __init__(self):
        """Initialize authentication service."""
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM

    def create_anonymous_user(self, db: Session, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or retrieve anonymous user.
        Uses device_id for returning anonymous users.
        """
        from main import UserDB  # Import here to avoid circular imports

        # If device_id provided, try to find existing anonymous user
        if device_id:
            existing_user = db.query(UserDB).filter(
                and_(
                    UserDB.device_id == device_id,
                    UserDB.is_anonymous == True
                )
            ).first()

            if existing_user:
                logger.info(f"Returning anonymous user found: {existing_user.id}")
                # Update last seen
                existing_user.last_seen = datetime.utcnow()
                db.commit()

                # Generate new tokens
                access_token = self.create_access_token({
                    "sub": existing_user.id,
                    "is_anonymous": True,
                    "device_id": device_id
                })
                refresh_token = self.create_refresh_token({
                    "sub": existing_user.id,
                    "device_id": device_id
                })

                return {
                    "user": existing_user,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "is_returning": True
                }

        # Create new anonymous user
        user_id = str(uuid.uuid4())
        new_device_id = device_id or str(uuid.uuid4())

        anonymous_user = UserDB(
            id=user_id,
            email=f"anonymous_{user_id}@eloquent.ai",
            username=f"anonymous_{user_id[:8]}",
            hashed_password="",  # No password for anonymous users
            is_anonymous=True,
            is_active=True,
            device_id=new_device_id,
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )

        db.add(anonymous_user)
        db.commit()
        db.refresh(anonymous_user)

        logger.info(f"New anonymous user created: {user_id}")

        # Generate tokens
        access_token = self.create_access_token({
            "sub": user_id,
            "is_anonymous": True,
            "device_id": new_device_id
        })
        refresh_token = self.create_refresh_token({
            "sub": user_id,
            "device_id": new_device_id
        })

        return {
            "user": anonymous_user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "is_returning": False
        }

    def convert_anonymous_to_registered(
        self,
        db: Session,
        anonymous_user_id: str,
        email: str,
        password: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert anonymous user to registered user."""
        from main import UserDB

        # Get anonymous user
        anonymous_user = db.query(UserDB).filter(
            and_(
                UserDB.id == anonymous_user_id,
                UserDB.is_anonymous == True
            )
        ).first()

        if not anonymous_user:
            raise ValueError("Anonymous user not found")

        # Check if email already exists
        existing_user = db.query(UserDB).filter(
            UserDB.email == email
        ).first()

        if existing_user and not existing_user.is_anonymous:
            raise ValueError("Email already registered")

        # Update anonymous user to registered
        anonymous_user.email = email
        anonymous_user.username = username or email.split('@')[0]
        anonymous_user.hashed_password = self.get_password_hash(password)
        anonymous_user.is_anonymous = False
        anonymous_user.converted_at = datetime.utcnow()

        db.commit()
        db.refresh(anonymous_user)

        logger.info(f"Anonymous user {anonymous_user_id} converted to registered user")

        # Generate new tokens
        access_token = self.create_access_token({
            "sub": anonymous_user.id,
            "email": email,
            "is_anonymous": False
        })
        refresh_token = self.create_refresh_token({
            "sub": anonymous_user.id,
            "email": email
        })

        return {
            "user": anonymous_user,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[Any]:
        """Authenticate registered user."""
        from main import UserDB

        user = db.query(UserDB).filter(
            and_(
                UserDB.email == email,
                UserDB.is_anonymous == False
            )
        ).first()

        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        # Update last seen
        user.last_seen = datetime.utcnow()
        db.commit()

        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # Different expiry for anonymous vs registered users
            if data.get("is_anonymous"):
                expire = datetime.utcnow() + timedelta(days=ANONYMOUS_TOKEN_EXPIRE_DAYS)
            else:
                expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Refresh access token using refresh token.
        Returns new access and refresh tokens.
        """
        payload = self.verify_token(refresh_token, token_type="refresh")

        if not payload:
            return None

        # Create new access token
        access_token = self.create_access_token({
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "is_anonymous": payload.get("is_anonymous", False),
            "device_id": payload.get("device_id")
        })

        # Create new refresh token
        new_refresh_token = self.create_refresh_token({
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "device_id": payload.get("device_id")
        })

        return access_token, new_refresh_token

    def get_password_hash(self, password: str) -> str:
        """Hash password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(plain_password, hashed_password)

    def track_user_activity(self, db: Session, user_id: str, activity_type: str, metadata: Dict[str, Any] = None):
        """Track user activity for analytics."""
        from main import UserActivityDB

        activity = UserActivityDB(
            user_id=user_id,
            activity_type=activity_type,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        db.add(activity)
        db.commit()

        logger.info(f"User activity tracked: {user_id} - {activity_type}")