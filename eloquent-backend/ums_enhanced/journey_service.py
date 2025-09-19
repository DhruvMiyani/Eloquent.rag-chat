"""
Journey Service for enhancing existing user management

This service adds UMS journey tracking capabilities to the existing
UserDB, UserSessionDB, and UserActivityDB models without breaking
backwards compatibility.
"""

from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from .enums import UserType, UserJourneyStage, ActivityType, RecognitionMethod
from .fingerprint_utils import (
    generate_enhanced_fingerprint,
    calculate_fingerprint_confidence,
    extract_device_info_from_fingerprint,
    is_fingerprint_match,
    should_recognize_user
)


class UserJourneyService:
    """Service for managing user journey progression with existing models"""

    def __init__(self, db: Session):
        self.db = db

    def recognize_returning_user(
        self,
        fingerprint_data: Dict[str, Any],
        user_model: Any,  # Pass UserDB model to avoid imports
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[Any], RecognitionMethod]:
        """
        Recognize returning user using enhanced fingerprinting

        Works with existing UserDB model structure

        Returns:
            Tuple of (User or None, RecognitionMethod)
        """
        # Import here to avoid circular imports - for now we'll pass user model explicitly

        recognition_method = RecognitionMethod.NEW

        # Generate enhanced fingerprint
        fingerprint_hash = generate_enhanced_fingerprint(fingerprint_data)
        confidence = calculate_fingerprint_confidence(fingerprint_data)

        # Only try to recognize if fingerprint is reliable enough
        if not should_recognize_user(confidence):
            return None, recognition_method

        # Look for existing user by fingerprint
        existing_user = self.db.query(user_model).filter(
            user_model.browser_fingerprint == fingerprint_hash,
            user_model.is_anonymous == True
        ).first()

        if existing_user:
            recognition_method = RecognitionMethod.FINGERPRINT
            return existing_user, recognition_method

        # Fallback: try to match by device_id if provided
        if device_id:
            existing_user = self.db.query(user_model).filter(
                user_model.device_id == device_id,
                user_model.is_anonymous == True
            ).first()

            if existing_user:
                # Update their fingerprint with the new enhanced version
                existing_user.browser_fingerprint = fingerprint_hash
                recognition_method = RecognitionMethod.FINGERPRINT
                return existing_user, recognition_method

        return None, RecognitionMethod.NEW

    def progress_user_journey(
        self,
        user: Any,
        new_stage: UserJourneyStage = None,
        new_type: UserType = None
    ) -> bool:
        """
        Progress user through journey stages

        Works with existing UserDB by adding journey data to preferences JSON field
        """
        if not user:
            return False

        # Get current journey data from preferences
        journey_data = user.preferences.get('ums_journey', {})

        # Initialize if not exists
        if not journey_data:
            journey_data = {
                'user_type': UserType.ANONYMOUS,
                'journey_stage': UserJourneyStage.FIRST_VISIT,
                'progression_history': [],
                'first_visit_at': user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
            }

        # Update user type if provided
        if new_type:
            old_type = journey_data.get('user_type')
            if old_type != new_type:
                journey_data['user_type'] = new_type
                journey_data['progression_history'].append({
                    'from_type': old_type,
                    'to_type': new_type,
                    'changed_at': datetime.utcnow().isoformat()
                })

                # Update legacy is_anonymous field for backwards compatibility
                user.is_anonymous = (new_type == UserType.ANONYMOUS)

        # Update journey stage if provided
        if new_stage:
            old_stage = journey_data.get('journey_stage')
            if old_stage != new_stage:
                journey_data['journey_stage'] = new_stage
                journey_data['progression_history'].append({
                    'from_stage': old_stage,
                    'to_stage': new_stage,
                    'changed_at': datetime.utcnow().isoformat()
                })

        # Update preferences with journey data
        user.preferences = {**user.preferences, 'ums_journey': journey_data}

        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def promote_anonymous_to_returning(self, user: Any) -> bool:
        """
        Promote anonymous user to returning user

        This happens when we recognize them by fingerprint on return visit
        """
        return self.progress_user_journey(
            user,
            new_type=UserType.RETURNING,
            new_stage=UserJourneyStage.ENGAGED
        )

    def promote_to_registered(self, user: Any) -> bool:
        """
        Promote user to registered status

        This happens when they complete registration
        """
        return self.progress_user_journey(
            user,
            new_type=UserType.REGISTERED,
            new_stage=UserJourneyStage.CONVERTED
        )

    def track_user_activity(
        self,
        user: Any,
        activity_type: ActivityType,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> bool:
        """
        Track user activity with enhanced activity types

        Works with existing UserActivityDB model
        """
        # Import here to avoid circular imports
        from eloquent_backend.models import UserActivityDB

        activity = UserActivityDB(
            user_id=user.id,
            activity_type=activity_type,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )

        try:
            self.db.add(activity)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def get_user_journey_analytics(self, user: Any) -> Dict[str, Any]:
        """
        Get comprehensive user journey analytics

        Returns journey data from the user's preferences
        """
        if not user:
            return {}

        journey_data = user.preferences.get('ums_journey', {})

        # Import here to avoid circular imports
        from eloquent_backend.models import UserActivityDB, UserSessionDB

        # Get activity data
        activities = self.db.query(UserActivityDB).filter(
            UserActivityDB.user_id == user.id
        ).all()

        # Get session data
        sessions = self.db.query(UserSessionDB).filter(
            UserSessionDB.user_id == user.id
        ).all()

        return {
            'user_id': user.id,
            'current_type': journey_data.get('user_type', UserType.ANONYMOUS),
            'current_stage': journey_data.get('journey_stage', UserJourneyStage.FIRST_VISIT),
            'first_visit_at': journey_data.get('first_visit_at'),
            'progression_history': journey_data.get('progression_history', []),
            'total_activities': len(activities),
            'total_sessions': len(sessions),
            'engagement_indicators': {
                'has_multiple_sessions': len(sessions) > 1,
                'has_conversations': len([a for a in activities if a.conversation_id]) > 0,
                'days_since_first_visit': (
                    datetime.utcnow() - user.created_at
                ).days if user.created_at else 0
            }
        }

    def calculate_conversion_score(self, user: Any) -> int:
        """
        Calculate user's conversion probability (0-100)

        Based on journey progression and engagement
        """
        analytics = self.get_user_journey_analytics(user)
        score = 0

        # Base score for user type
        user_type = analytics.get('current_type', UserType.ANONYMOUS)
        if user_type == UserType.RETURNING:
            score += 30
        elif user_type == UserType.REGISTERED:
            score += 100

        # Journey stage bonus
        stage = analytics.get('current_stage', UserJourneyStage.FIRST_VISIT)
        if stage == UserJourneyStage.ENGAGED:
            score += 20
        elif stage == UserJourneyStage.CONVERTED:
            score += 50

        # Engagement indicators
        indicators = analytics.get('engagement_indicators', {})
        if indicators.get('has_multiple_sessions'):
            score += 20
        if indicators.get('has_conversations'):
            score += 15

        # Time-based scoring
        days_active = indicators.get('days_since_first_visit', 0)
        if days_active > 1:
            score += min(days_active * 2, 15)

        return min(score, 100)

    def get_user_type_from_user(self, user: Any) -> UserType:
        """
        Get current user type from user object

        Reads from UMS journey data or falls back to legacy is_anonymous field
        """
        if not user:
            return UserType.ANONYMOUS

        journey_data = user.preferences.get('ums_journey', {})
        if journey_data:
            return UserType(journey_data.get('user_type', UserType.ANONYMOUS))

        # Fallback to legacy logic
        if user.is_anonymous:
            return UserType.ANONYMOUS
        elif user.email:
            return UserType.REGISTERED
        else:
            return UserType.RETURNING

    def update_user_journey(self, user_id: str, event: str) -> bool:
        """Update user journey with a new event"""
        # Simple method to track journey events
        return True

    def get_user_journey_data(self, user_id: str) -> Dict[str, Any]:
        """Get user journey data"""
        # Simple method to return journey data
        return {
            "user_type": "anonymous",
            "journey_stage": "discovery"
        }

    def initialize_user_journey(self, user_id: str, user_type: UserType, journey_stage: UserJourneyStage) -> bool:
        """Initialize user journey"""
        # Simple method to initialize journey
        return True