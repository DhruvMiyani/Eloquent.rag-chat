"""
Example integration showing how to enhance existing auth endpoints with UMS

This example shows how to add UMS journey tracking and enhanced fingerprinting
to the existing /api/auth endpoints without breaking backwards compatibility.
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json

# Import existing models (adjust import path as needed)
# from eloquent_backend.models import UserDB, UserSessionDB
# from eloquent_backend.database import get_db

# Import UMS enhanced services
from .journey_service import UserJourneyService
from .fingerprint_utils import (
    generate_enhanced_fingerprint,
    calculate_fingerprint_confidence,
    extract_device_info_from_fingerprint
)
from .enums import UserType, UserJourneyStage, ActivityType, RecognitionMethod


def enhance_anonymous_auth_endpoint(
    device_id: Optional[str] = None,
    browser_fingerprint: Optional[str] = None,
    raw_fingerprint_data: Optional[Dict[str, Any]] = None,
    device_info: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),  # Your existing database dependency
    request: Request = None
):
    """
    Enhanced version of /api/auth/anonymous endpoint

    This function can be used to replace or enhance the existing anonymous auth logic
    """
    # Initialize UMS journey service
    journey_service = UserJourneyService(db)

    # Extract request information
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    # Enhanced fingerprinting if raw data provided
    enhanced_fingerprint = None
    fingerprint_confidence = 0
    recognition_method = RecognitionMethod.NEW

    if raw_fingerprint_data:
        # Generate enhanced fingerprint
        enhanced_fingerprint = generate_enhanced_fingerprint(raw_fingerprint_data)
        fingerprint_confidence = calculate_fingerprint_confidence(raw_fingerprint_data)

        # Try to recognize returning user
        existing_user, recognition_method = journey_service.recognize_returning_user(
            raw_fingerprint_data, device_id, ip_address
        )

        if existing_user:
            # Update their journey - promote to returning user
            journey_service.promote_anonymous_to_returning(existing_user)

            # Track return visit activity
            journey_service.track_user_activity(
                existing_user,
                ActivityType.SESSION_START,
                metadata={
                    'recognition_method': recognition_method,
                    'fingerprint_confidence': fingerprint_confidence,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )

            # Update session information
            existing_user.last_seen = datetime.utcnow()
            existing_user.ip_address = ip_address

            # Update enhanced fingerprint if confidence improved
            if enhanced_fingerprint and fingerprint_confidence > 60:
                existing_user.browser_fingerprint = enhanced_fingerprint

            db.commit()

            # Return enhanced response
            return create_enhanced_auth_response(
                existing_user,
                recognition_method,
                fingerprint_confidence,
                is_returning=True
            )

    # Create new anonymous user (existing logic with UMS enhancements)
    new_user = create_new_anonymous_user(
        device_id=device_id,
        browser_fingerprint=enhanced_fingerprint or browser_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info,
        db=db
    )

    # Initialize UMS journey tracking
    journey_service.progress_user_journey(
        new_user,
        new_type=UserType.ANONYMOUS,
        new_stage=UserJourneyStage.FIRST_VISIT
    )

    # Track first visit
    journey_service.track_user_activity(
        new_user,
        ActivityType.FIRST_VISIT,
        metadata={
            'fingerprint_confidence': fingerprint_confidence,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
    )

    return create_enhanced_auth_response(
        new_user,
        RecognitionMethod.NEW,
        fingerprint_confidence,
        is_returning=False
    )


def enhance_user_registration_endpoint(
    email: str,
    password: str,
    name: Optional[str] = None,
    current_user_id: Optional[str] = None,  # From existing auth
    db: Session = Depends(get_db)
):
    """
    Enhanced version of user registration that includes UMS journey tracking

    This can enhance the existing /api/auth/register endpoint
    """
    journey_service = UserJourneyService(db)

    # If converting anonymous user
    if current_user_id:
        # Import your existing User model
        # from eloquent_backend.models import UserDB

        existing_user = db.query(UserDB).filter(UserDB.id == current_user_id).first()
        if existing_user and existing_user.is_anonymous:
            # Convert anonymous to registered
            existing_user.email = email
            existing_user.hashed_password = hash_password(password)  # Your existing hash function
            existing_user.name = name
            existing_user.is_anonymous = False

            # Update UMS journey
            journey_service.promote_to_registered(existing_user)

            # Track conversion activity
            journey_service.track_user_activity(
                existing_user,
                ActivityType.USER_REGISTRATION,
                metadata={
                    'conversion_from': 'anonymous',
                    'email': email
                }
            )

            db.commit()

            return create_enhanced_auth_response(
                existing_user,
                RecognitionMethod.EMAIL_LOGIN,
                100,  # High confidence for registered user
                is_returning=True,
                is_converted=True
            )

    # Create new registered user (existing logic)
    new_user = create_new_registered_user(email, password, name, db)

    # Initialize UMS journey for direct registration
    journey_service.progress_user_journey(
        new_user,
        new_type=UserType.REGISTERED,
        new_stage=UserJourneyStage.CONVERTED
    )

    return create_enhanced_auth_response(
        new_user,
        RecognitionMethod.NEW,
        100,
        is_returning=False,
        is_converted=True
    )


def create_enhanced_auth_response(
    user,
    recognition_method: RecognitionMethod,
    fingerprint_confidence: int,
    is_returning: bool = False,
    is_converted: bool = False
) -> Dict[str, Any]:
    """
    Create enhanced authentication response with UMS data

    Maintains backwards compatibility while adding UMS insights
    """
    journey_service = UserJourneyService(db)  # You'd need to pass db here

    # Get UMS journey analytics
    analytics = journey_service.get_user_analytics(user)

    # Create backwards-compatible response
    response = {
        # Existing response format
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_anonymous": user.is_anonymous,
            "created_at": user.created_at
        },
        "token": generate_jwt_token(user),  # Your existing token generation

        # UMS enhancements (optional fields)
        "ums_data": {
            "user_type": analytics.get('current_type'),
            "journey_stage": analytics.get('current_stage'),
            "recognition_method": recognition_method,
            "fingerprint_confidence": fingerprint_confidence,
            "is_returning": is_returning,
            "is_converted": is_converted,
            "conversion_score": journey_service.calculate_conversion_score(user),
            "engagement_indicators": analytics.get('engagement_indicators', {})
        }
    }

    return response


def get_enhanced_user_analytics_endpoint(
    user_id: str,
    current_user = Depends(get_current_user),  # Your existing auth dependency
    db: Session = Depends(get_db)
):
    """
    New endpoint for getting UMS analytics

    Can be added as /api/ums/analytics/{user_id}
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    journey_service = UserJourneyService(db)
    analytics = journey_service.get_user_analytics(current_user)

    return {
        "user_id": user_id,
        "journey_analytics": analytics,
        "conversion_score": journey_service.calculate_conversion_score(current_user),
        "recommendations": generate_user_recommendations(analytics)
    }


def generate_user_recommendations(analytics: Dict[str, Any]) -> list[str]:
    """Generate personalized recommendations based on UMS analytics"""
    recommendations = []

    user_type = analytics.get('current_type', UserType.ANONYMOUS)
    engagement = analytics.get('engagement_indicators', {})

    if user_type == UserType.ANONYMOUS:
        if engagement.get('has_multiple_sessions'):
            recommendations.append("You're becoming a regular! Consider creating an account to save your chat history.")
        if engagement.get('days_since_first_visit', 0) > 1:
            recommendations.append("Welcome back! Register to unlock premium features.")

    elif user_type == UserType.RETURNING:
        recommendations.append("You're recognized as a returning user. Create an account to secure your data.")
        if analytics.get('total_sessions', 0) > 5:
            recommendations.append("You're an active user! Registration unlocks advanced features.")

    return recommendations


# Example of how to integrate with existing FastAPI app
def integrate_ums_with_existing_app(app: FastAPI):
    """
    Example of how to integrate UMS enhancements with existing FastAPI app
    """

    # Replace existing anonymous auth endpoint
    @app.post("/api/auth/anonymous", response_model=dict)
    async def enhanced_anonymous_auth(request: Request, db: Session = Depends(get_db)):
        # Get request data
        data = await request.json()

        return enhance_anonymous_auth_endpoint(
            device_id=data.get('device_id'),
            browser_fingerprint=data.get('browser_fingerprint'),
            raw_fingerprint_data=data.get('raw_fingerprint_data'),
            device_info=data.get('device_info'),
            db=db,
            request=request
        )

    # Add new UMS analytics endpoint
    @app.get("/api/ums/analytics/{user_id}")
    async def user_analytics(user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
        return get_enhanced_user_analytics_endpoint(user_id, current_user, db)

    # Add UMS journey tracking endpoint
    @app.get("/api/ums/journey/{user_id}")
    async def user_journey(user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        journey_service = UserJourneyService(db)
        analytics = journey_service.get_user_analytics(current_user)

        return {
            "user_id": user_id,
            "current_type": analytics.get('current_type'),
            "current_stage": analytics.get('current_stage'),
            "progression_history": analytics.get('progression_history', []),
            "recommendations": generate_user_recommendations(analytics)
        }


# Helper functions (you would implement these based on your existing code)
def create_new_anonymous_user(device_id, browser_fingerprint, ip_address, user_agent, device_info, db):
    """Create new anonymous user - implement based on your existing logic"""
    pass

def create_new_registered_user(email, password, name, db):
    """Create new registered user - implement based on your existing logic"""
    pass

def hash_password(password):
    """Hash password - use your existing implementation"""
    pass

def generate_jwt_token(user):
    """Generate JWT token - use your existing implementation"""
    pass

def get_current_user():
    """Get current user dependency - use your existing implementation"""
    pass

def get_db():
    """Database dependency - use your existing implementation"""
    pass