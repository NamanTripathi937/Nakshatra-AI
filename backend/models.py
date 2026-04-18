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
    user_id: Optional[str] = None
    plan_snapshot: Optional[str] = None
    full_name: Optional[str] = None
    birth_details: Optional[Dict[str, Any]] = None  # year, month, date, hours, minutes, seconds, lat, lon, timezone
    messages: List[Message] = Field(default_factory=list)  # All chat messages for this session
    message_count: int = 0
    last_message_preview: str = ""
    last_message_role: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserData(BaseModel):
    google_sub: str
    email: str
    name: str
    picture: Optional[str] = None
    plan: str = "free"
    billing: Dict[str, Any] = Field(default_factory=dict)
    usage: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentRecord(BaseModel):
    order_id: str
    user_id: str
    provider: str = "razorpay"
    plan_code: str
    plan_name: str
    amount_paise: int
    currency: str = "INR"
    status: str = "created"
    activated: bool = False
    payment_id: Optional[str] = None
    receipt: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
