"""
User Management Services (UMS) Module

This module provides comprehensive user management capabilities including:
- Anonymous user tracking and recognition
- Session management with browser fingerprinting
- User journey tracking (anonymous -> returning -> registered)
- Authentication and authorization
- RESTful API endpoints for FastAPI integration
"""

from .models.user import User, UserSession, UserFingerprint, UserType, UserJourneyStage
from .services.session_service import SessionService
from .services.user_service import UserService
from .schemas.user_schemas import (
    UserCreate, UserLogin, UserConvert, SessionCreate,
    UserResponse, UserWithSessionResponse, AuthResponse,
    SessionResponse, FingerprintResponse, UserStatsResponse, UserJourneyResponse
)
from .api.routes import router as ums_router

__version__ = "1.0.0"
__all__ = [
    # Models
    "User", "UserSession", "UserFingerprint",
    "UserType", "UserJourneyStage",

    # Services
    "SessionService", "UserService",

    # Schemas
    "UserCreate", "UserLogin", "UserConvert", "SessionCreate",
    "UserResponse", "UserWithSessionResponse", "AuthResponse",
    "SessionResponse", "FingerprintResponse", "UserStatsResponse", "UserJourneyResponse",

    # API Router
    "ums_router"
]