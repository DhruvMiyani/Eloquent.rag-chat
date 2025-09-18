"""
Enhanced Database Models for User Management
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Text, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class UserDB(Base):
    """Enhanced user model with anonymous and registered user support."""
    __tablename__ = "users"

    # Core fields
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    hashed_password = Column(String)

    # User type and status
    is_anonymous = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Device tracking for anonymous users
    device_id = Column(String, index=True)
    browser_fingerprint = Column(String)
    ip_address = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    converted_at = Column(DateTime)  # When anonymous user converted to registered

    # User preferences
    preferences = Column(JSON, default=dict)

    # Relationships
    conversations = relationship("ConversationDB", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivityDB", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSessionDB", back_populates="user", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_device_anonymous', 'device_id', 'is_anonymous'),
        Index('idx_email_anonymous', 'email', 'is_anonymous'),
    )

class UserSessionDB(Base):
    """Track user sessions for security and analytics."""
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    # Session details
    access_token_jti = Column(String, index=True)  # JWT ID for tracking
    refresh_token_jti = Column(String, index=True)

    # Device information
    user_agent = Column(String)
    ip_address = Column(String)
    device_type = Column(String)  # mobile, tablet, desktop
    browser = Column(String)
    os = Column(String)

    # Session lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Security
    logout_at = Column(DateTime)
    logout_reason = Column(String)  # manual, expired, security

    # Relationship
    user = relationship("UserDB", back_populates="sessions")

class UserActivityDB(Base):
    """Track user activities for analytics and recommendations."""
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))

    # Activity details
    activity_type = Column(String, index=True)  # chat_start, message_sent, feedback, etc.
    activity_subtype = Column(String)

    # Context
    conversation_id = Column(String, ForeignKey("conversations.id"))
    message_id = Column(String, ForeignKey("messages.id"))

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_seconds = Column(Integer)

    # Relationships
    user = relationship("UserDB", back_populates="activities")

class ConversationDB(Base):
    """Enhanced conversation model with better tracking."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)

    # Conversation metadata
    context = Column(JSON, default=dict)
    tags = Column(JSON, default=list)

    # Statistics
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime)

    # Soft delete
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime)

    # Relationships
    user = relationship("UserDB", back_populates="conversations")
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_user_archived', 'user_id', 'is_archived'),
    )

class MessageDB(Base):
    """Enhanced message model with better metadata."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))

    # Message content
    content = Column(Text)
    sender = Column(String)  # user, assistant, system

    # RAG context
    context_used = Column(JSON, default=list)  # FAQ IDs used for response
    confidence_score = Column(String)  # RAG confidence

    # Metadata
    metadata = Column(JSON, default=dict)

    # Token tracking
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    edited_at = Column(DateTime)

    # User feedback
    feedback_rating = Column(Integer)  # 1-5 star rating
    feedback_text = Column(Text)
    feedback_at = Column(DateTime)

    # Relationships
    conversation = relationship("ConversationDB", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
    )

class SystemConfigDB(Base):
    """Store system configuration and feature flags."""
    __tablename__ = "system_config"

    key = Column(String, primary_key=True)
    value = Column(JSON)

    # Metadata
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String)

class AuditLogDB(Base):
    """Audit log for compliance and security."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event details
    event_type = Column(String, index=True)
    event_subtype = Column(String)
    severity = Column(String)  # info, warning, error, critical

    # User context
    user_id = Column(String, ForeignKey("users.id"))
    ip_address = Column(String)
    user_agent = Column(String)

    # Event data
    resource_type = Column(String)  # user, conversation, message, etc.
    resource_id = Column(String)
    before_value = Column(JSON)
    after_value = Column(JSON)
    metadata = Column(JSON, default=dict)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_event_created', 'event_type', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )