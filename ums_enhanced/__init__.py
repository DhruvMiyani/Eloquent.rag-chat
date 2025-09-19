"""
UMS Enhanced Module

Modular enhancements for the existing user management system.
Provides journey tracking and enhanced fingerprinting while maintaining
backwards compatibility with the current database schema.
"""

from .enums import UserType, UserJourneyStage, ActivityType, RecognitionMethod

__version__ = "1.0.0"
__all__ = [
    "UserType",
    "UserJourneyStage",
    "ActivityType",
    "RecognitionMethod"
]