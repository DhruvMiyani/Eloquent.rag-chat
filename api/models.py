"""Data models for the API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    chat_id: Optional[str] = Field(None, description="Chat session ID")
    user_id: Optional[str] = Field(None, description="User ID for authenticated users")
    device_id: Optional[str] = Field(None, description="Device ID for anonymous users")

class Citation(BaseModel):
    id: str
    text: str
    category: str
    relevance_score: float

class Message(BaseModel):
    id: Optional[str] = None
    chat_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    citations: Optional[List[Citation]] = None

class ChatResponse(BaseModel):
    chat_id: str
    answer: str
    citations: List[Citation]
    messages: List[Message]

class Chat(BaseModel):
    id: str
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None

class ChatListResponse(BaseModel):
    chats: List[Chat]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, bool]