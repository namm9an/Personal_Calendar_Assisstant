"""
User model and related schemas.
"""
import uuid
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, Column, DateTime, String, Time
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.types import UniversalUUID


class User(Base):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Time zone and working hours
    timezone = Column(String, default="UTC")
    working_hours_start = Column(Time, default=time(9, 0))  # Default to 9:00 AM
    working_hours_end = Column(Time, default=time(17, 0))   # Default to 5:00 PM
    
    # OAuth credentials
    google_id = Column(String, unique=True, index=True, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)
    microsoft_id = Column(String, unique=True, index=True, nullable=True)
    microsoft_access_token = Column(String, nullable=True)
    microsoft_refresh_token = Column(String, nullable=True)
    microsoft_token_expiry = Column(DateTime, nullable=True)
    
    # User preferences for agent behavior as JSON
    preferences = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


# Pydantic models for API
class UserBase(BaseModel):
    """Base fields for user schemas."""
    email: EmailStr
    name: Optional[str] = None
    timezone: str = "UTC"
    working_hours_start: time = Field(default_factory=lambda: time(9, 0))
    working_hours_end: time = Field(default_factory=lambda: time(17, 0))
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    timezone: Optional[str] = None
    working_hours_start: Optional[time] = None
    working_hours_end: Optional[time] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user in database, including internal fields."""
    id: uuid.UUID
    is_active: bool
    google_id: Optional[str] = None
    microsoft_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user API responses."""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
