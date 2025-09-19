"""
Pydantic schemas for User Management Services (UMS)

This module defines the request/response schemas for the UMS API
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


class FingerprintCreate(BaseModel):
    """Schema for creating a browser fingerprint"""
    browser_name: Optional[str] = None
    browser_version: Optional[str] = None
    os_name: Optional[str] = None
    device_type: Optional[str] = None
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    components: Dict[str, Any] = {}  # Raw fingerprint components


class SessionCreate(BaseModel):
    """Schema for creating a user session"""
    fingerprint: Optional[FingerprintCreate] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    name: Optional[str] = None
    session_info: Optional[SessionCreate] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    session_info: Optional[SessionCreate] = None


class UserConvert(BaseModel):
    """Schema for converting anonymous user to registered"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class FingerprintResponse(BaseModel):
    """Schema for fingerprint response"""
    id: str
    fingerprint_hash: str
    browser_name: Optional[str]
    browser_version: Optional[str]
    os_name: Optional[str]
    device_type: Optional[str]
    confidence_score: int
    first_seen_at: datetime
    last_seen_at: datetime
    times_seen: int

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: str
    session_token: str
    is_active: bool
    started_at: datetime
    last_activity_at: datetime
    messages_sent: int
    session_duration: int

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: Optional[str]
    name: Optional[str]
    user_type: str
    journey_stage: str
    is_anonymous: bool
    first_visit_at: datetime
    last_seen_at: datetime
    total_sessions: int
    total_messages: int
    engagement_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithSessionResponse(BaseModel):
    """Schema for user response with session info"""
    user: UserResponse
    session: SessionResponse
    fingerprint: Optional[FingerprintResponse] = None
    is_returning: bool = False
    recognition_method: Optional[str] = None  # "fingerprint", "session", "new"


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    session: SessionResponse
    is_returning: bool = False


class UserStatsResponse(BaseModel):
    """Schema for user statistics"""
    total_users: int
    anonymous_users: int
    returning_users: int
    registered_users: int
    active_sessions: int
    avg_engagement_score: float


class UserJourneyResponse(BaseModel):
    """Schema for user journey tracking"""
    user_id: str
    journey_events: List[Dict[str, Any]]
    current_stage: str
    progression_score: int
    recommendations: List[str]