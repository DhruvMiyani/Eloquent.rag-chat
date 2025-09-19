"""
UMS API Routes for User Management Services

This module provides the FastAPI routes for the UMS module,
handling anonymous user flow, authentication, and user conversion.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ..services.user_service import UserService
from ..schemas.user_schemas import (
    UserCreate, UserLogin, UserConvert, SessionCreate,
    UserResponse, UserWithSessionResponse, AuthResponse,
    UserStatsResponse, UserJourneyResponse
)
from ..models.user import User


# Create router
router = APIRouter(prefix="/api/ums", tags=["User Management"])
security = HTTPBearer(auto_error=False)


def get_db() -> Session:
    """
    Dependency to get database session
    This should be replaced with your app's database dependency
    """
    # TODO: Import from main app's database configuration
    # For now, this is a placeholder
    pass


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current authenticated user
    """
    if not credentials:
        return None

    user_service = UserService(db)
    return user_service.get_user_by_token(credentials.credentials)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get UserService instance"""
    return UserService(db)


@router.post("/session/anonymous", response_model=UserWithSessionResponse)
async def create_anonymous_session(
    session_data: SessionCreate,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create or retrieve anonymous user session with fingerprint recognition

    This endpoint handles the anonymous user flow:
    1. Check if user exists by browser fingerprint
    2. If exists, return existing user as "returning"
    3. If not, create new anonymous user
    """
    # Extract request metadata
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")

    # Create or get user with session
    return user_service.create_anonymous_user(session_data, client_ip, user_agent)


@router.post("/auth/session", response_model=UserWithSessionResponse)
async def authenticate_by_session(
    session_token: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate user by existing session token

    This is used when a user returns with a stored session token
    """
    result = user_service.authenticate_by_session(session_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    return result


@router.post("/auth/register", response_model=AuthResponse)
async def register_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user account

    Creates a new registered user with credentials
    """
    return user_service.register_user(user_data)


@router.post("/auth/login", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    Login existing registered user

    Authenticates user with email/password and creates new session
    """
    return user_service.login_user(login_data)


@router.post("/auth/convert", response_model=AuthResponse)
async def convert_anonymous_user(
    convert_data: UserConvert,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Convert anonymous user to registered user

    Allows anonymous users to register and maintain their session history
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    return user_service.convert_anonymous_to_registered(current_user.id, convert_data)


@router.post("/auth/logout")
async def logout_user(
    session_token: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    Logout user by invalidating session
    """
    success = user_service.logout_user(session_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Logged out successfully"}


@router.get("/user/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return UserResponse.from_orm(current_user)


@router.get("/user/{user_id}/analytics")
async def get_user_analytics(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get comprehensive user analytics and journey data

    Only accessible by the user themselves or admin users
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check if user can access this data (self or admin)
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return user_service.get_user_analytics(user_id)


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    user_service: UserService = Depends(get_user_service)
):
    """
    Get overall user statistics (public endpoint for dashboard)
    """
    # This would typically be restricted to admin users
    # For now, we'll provide basic stats

    db = user_service.db
    from ..models.user import User, UserSession, UserType

    total_users = db.query(User).count()
    anonymous_users = db.query(User).filter(User.user_type == UserType.ANONYMOUS).count()
    returning_users = db.query(User).filter(User.user_type == UserType.RETURNING).count()
    registered_users = db.query(User).filter(User.user_type == UserType.REGISTERED).count()
    active_sessions = db.query(UserSession).filter(UserSession.is_active == True).count()

    # Calculate average engagement score
    avg_engagement = db.query(User).with_entities(
        db.func.avg(User.engagement_score)
    ).scalar() or 0.0

    return UserStatsResponse(
        total_users=total_users,
        anonymous_users=anonymous_users,
        returning_users=returning_users,
        registered_users=registered_users,
        active_sessions=active_sessions,
        avg_engagement_score=float(avg_engagement)
    )


@router.get("/user/{user_id}/journey", response_model=UserJourneyResponse)
async def get_user_journey(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user journey tracking and recommendations
    """
    if not current_user or current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get user analytics
    analytics = user_service.get_user_analytics(user_id)

    # Generate journey events (simplified for this implementation)
    journey_events = [
        {
            "event": "first_visit",
            "timestamp": current_user.first_visit_at.isoformat(),
            "data": {"user_type": "anonymous"}
        }
    ]

    if current_user.user_type != "anonymous":
        journey_events.append({
            "event": "user_recognition",
            "timestamp": current_user.last_seen_at.isoformat(),
            "data": {"recognition_method": "fingerprint"}
        })

    if current_user.user_type == "registered":
        journey_events.append({
            "event": "user_conversion",
            "timestamp": current_user.updated_at.isoformat(),
            "data": {"conversion_type": "registration"}
        })

    # Generate recommendations based on user stage
    recommendations = _generate_user_recommendations(current_user, analytics)

    return UserJourneyResponse(
        user_id=user_id,
        journey_events=journey_events,
        current_stage=current_user.journey_stage,
        progression_score=analytics.get('conversion_funnel', {}).get('conversion_potential', 0),
        recommendations=recommendations
    )


def _generate_user_recommendations(user: User, analytics: Dict[str, Any]) -> list[str]:
    """Generate personalized recommendations for user"""
    recommendations = []

    engagement_score = analytics.get('engagement_score', 0)
    total_sessions = analytics.get('total_sessions', 0)

    if user.user_type == "anonymous":
        if engagement_score > 10:
            recommendations.append("Consider creating an account to save your chat history")
        if total_sessions > 3:
            recommendations.append("You're a frequent user! Register to unlock premium features")

    elif user.user_type == "returning":
        if total_sessions > 5:
            recommendations.append("Register to ensure your data is always safe")
        recommendations.append("Explore our advanced features by creating an account")

    else:  # registered
        if engagement_score < 20:
            recommendations.append("Try asking about our new features")
        recommendations.append("Share feedback to help us improve")

    return recommendations