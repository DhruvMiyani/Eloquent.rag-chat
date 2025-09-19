"""
UMS Enums for enhancing existing user models

These enums add journey tracking capabilities to the existing system
without breaking current functionality.
"""

from enum import Enum


class UserType(str, Enum):
    """Enhanced user type enumeration for journey tracking"""
    ANONYMOUS = "anonymous"
    RETURNING = "returning"
    REGISTERED = "registered"


class UserJourneyStage(str, Enum):
    """User journey stage enumeration"""
    FIRST_VISIT = "first_visit"
    ENGAGED = "engaged"
    CONVERTED = "converted"


class ActivityType(str, Enum):
    """Enhanced activity types for better tracking"""
    FIRST_VISIT = "first_visit"
    CHAT_START = "chat_start"
    MESSAGE_SENT = "message_sent"
    FEEDBACK_GIVEN = "feedback_given"
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class RecognitionMethod(str, Enum):
    """Method used to recognize returning users"""
    NEW = "new"
    FINGERPRINT = "fingerprint"
    SESSION_TOKEN = "session_token"
    EMAIL_LOGIN = "email_login"