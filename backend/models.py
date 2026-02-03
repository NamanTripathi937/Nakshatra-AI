from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Model for individual chat message"""
    role: str  # 'user' or 'assistant'
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionData(BaseModel):
    """Unified model for session data including name, birth details and chat history"""
    session_id: str
    full_name: Optional[str] = None
    birth_details: Optional[Dict[str, Any]] = None  # year, month, date, hours, minutes, seconds, lat, lon, timezone
    messages: List[Message] = []  # All chat messages for this session
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
