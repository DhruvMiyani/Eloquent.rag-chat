"""
Enhanced User models for the User Management Services (UMS)

This module defines the database models for:
- User: Enhanced user model with journey tracking
- UserSession: Session management for anonymous and returning users
- UserFingerprint: Browser fingerprinting for user recognition
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

Base = declarative_base()


class UserType(str, Enum):
    """User type enumeration"""
    ANONYMOUS = "anonymous"
    RETURNING = "returning"
    REGISTERED = "registered"


class UserJourneyStage(str, Enum):
    """User journey stage enumeration"""
    FIRST_VISIT = "first_visit"
    ENGAGED = "engaged"
    CONVERTED = "converted"


class User(Base):
    """
    Enhanced User model with journey tracking and session management

    Supports the full user journey:
    - Anonymous users (first-time visitors)
    - Returning users (recognized by fingerprint/session)
    - Registered users (with credentials)
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic user information
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    name = Column(String, nullable=True)

    # User type and journey tracking
    user_type = Column(String, default=UserType.ANONYMOUS)  # anonymous, returning, registered
    journey_stage = Column(String, default=UserJourneyStage.FIRST_VISIT)  # first_visit, engaged, converted

    # Legacy support
    is_anonymous = Column(Boolean, default=True)

    # Enhanced tracking
    first_visit_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    total_sessions = Column(Integer, default=1)
    total_messages = Column(Integer, default=0)

    # User engagement metrics
    engagement_score = Column(Integer, default=0)  # Based on activity
    preferred_topics = Column(JSON, nullable=True)  # AI-detected interests

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    fingerprints = relationship("UserFingerprint", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user")

    def update_last_seen(self):
        """Update last seen timestamp and session count"""
        self.last_seen_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_engagement(self, points: int = 1):
        """Increment engagement score"""
        self.engagement_score += points
        self.updated_at = datetime.utcnow()

    def promote_to_returning(self):
        """Promote anonymous user to returning user"""
        if self.user_type == UserType.ANONYMOUS:
            self.user_type = UserType.RETURNING
            self.is_anonymous = False
            self.journey_stage = UserJourneyStage.ENGAGED
            self.updated_at = datetime.utcnow()

    def promote_to_registered(self, email: str, hashed_password: str, name: str = None):
        """Promote user to registered status"""
        self.email = email
        self.hashed_password = hashed_password
        self.name = name
        self.user_type = UserType.REGISTERED
        self.is_anonymous = False
        self.journey_stage = UserJourneyStage.CONVERTED
        self.updated_at = datetime.utcnow()


class UserSession(Base):
    """
    User session tracking for anonymous and returning user recognition
    """
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Session identification
    session_token = Column(String, unique=True, index=True, nullable=False)
    fingerprint_hash = Column(String, index=True, nullable=True)

    # Session details
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)

    # Session activity
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Activity tracking
    page_views = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    session_duration = Column(Integer, default=0)  # in seconds

    # Relationships
    user = relationship("User", back_populates="sessions")

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()

    def increment_messages(self):
        """Increment message count for this session"""
        self.messages_sent += 1
        self.update_activity()

    def calculate_duration(self):
        """Calculate session duration in seconds"""
        if self.last_activity_at and self.started_at:
            delta = self.last_activity_at - self.started_at
            self.session_duration = int(delta.total_seconds())
        return self.session_duration


class UserFingerprint(Base):
    """
    Browser fingerprinting for anonymous user recognition

    This helps identify returning users even without cookies/login
    """
    __tablename__ = "user_fingerprints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Fingerprint data
    fingerprint_hash = Column(String, unique=True, index=True, nullable=False)
    raw_fingerprint = Column(JSON, nullable=False)

    # Browser/Device information
    browser_name = Column(String, nullable=True)
    browser_version = Column(String, nullable=True)
    os_name = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet

    # Screen information
    screen_resolution = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    language = Column(String, nullable=True)

    # Fingerprint strength and reliability
    confidence_score = Column(Integer, default=50)  # 0-100, higher = more reliable
    components_count = Column(Integer, default=0)  # Number of fingerprint components

    # Tracking
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    times_seen = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="fingerprints")

    def update_seen(self):
        """Update last seen and increment times seen"""
        self.last_seen_at = datetime.utcnow()
        self.times_seen += 1

    def calculate_confidence(self):
        """Calculate confidence score based on fingerprint components"""
        base_score = min(self.components_count * 5, 70)  # Up to 70 for components
        stability_bonus = min(self.times_seen * 2, 30)  # Up to 30 for stability
        self.confidence_score = min(base_score + stability_bonus, 100)
        return self.confidence_score


# For backward compatibility with existing code
class Conversation(Base):
    """Conversation model (placeholder - should be defined in main app)"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")