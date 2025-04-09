from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    """Base session schema."""
    title: str


class SessionCreate(SessionBase):
    """Schema for creating a session."""
    pass


class SessionResponse(SessionBase):
    """Schema for session response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """Base message schema."""
    content: str
    role: str


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    context_chunks: Optional[str] = None


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: UUID
    session_id: UUID
    created_at: datetime
    context_chunks: Optional[str] = None

    class Config:
        from_attributes = True


class ChatSessionResponse(SessionResponse):
    """Schema for chat session with messages."""
    messages: List[MessageResponse]

    class Config:
        from_attributes = True
