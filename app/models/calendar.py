"""
Calendar models and related schemas.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (Boolean, Column, DateTime, Enum as SQLAlchemyEnum,
                        ForeignKey, String, Text)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.types import UniversalUUID


class CalendarProvider(str, Enum):
    """Enum for calendar providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class CalendarActionType(str, Enum):
    """Enum for calendar action types."""
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    AVAILABILITY = "availability"


class CalendarAction(Base):
    """Calendar action audit log model."""
    
    __tablename__ = "calendar_actions"
    
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    
    # User who performed the action
    user_id = Column(UniversalUUID, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="calendar_actions")
    
    # Action details
    provider = Column(SQLAlchemyEnum(CalendarProvider), nullable=False)
    action_type = Column(SQLAlchemyEnum(CalendarActionType), nullable=False)
    
    # Event details (if applicable)
    event_id = Column(String, nullable=True)
    event_summary = Column(String, nullable=True)
    event_start = Column(DateTime(timezone=True), nullable=True)
    event_end = Column(DateTime(timezone=True), nullable=True)
    
    # Natural language input that triggered the action
    user_input = Column(Text, nullable=True)
    
    # Response from the calendar provider
    provider_response = Column(JSON, nullable=True)
    
    # Success status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<CalendarAction {self.action_type} by {self.user_id}>"


class UserCalendar(Base):
    """User calendar configuration model."""
    
    __tablename__ = "user_calendars"
    
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    
    # User who owns this calendar
    user_id = Column(UniversalUUID, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="calendars")
    
    # Calendar details
    provider = Column(SQLAlchemyEnum(CalendarProvider), nullable=False)
    calendar_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Calendar-specific settings
    is_primary = Column(Boolean, default=False)
    is_selected = Column(Boolean, default=True)
    color = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<UserCalendar {self.name} ({self.provider})>"


# Pydantic models for API
class CalendarActionBase(BaseModel):
    """Base fields for calendar action schemas."""
    provider: CalendarProvider
    action_type: CalendarActionType
    event_id: Optional[str] = None
    event_summary: Optional[str] = None
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
    user_input: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class CalendarActionCreate(CalendarActionBase):
    """Schema for creating a new calendar action log."""
    user_id: uuid.UUID


class CalendarActionResponse(CalendarActionBase):
    """Schema for calendar action API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserCalendarBase(BaseModel):
    """Base fields for user calendar schemas."""
    provider: CalendarProvider
    calendar_id: str
    name: str
    description: Optional[str] = None
    is_primary: bool = False
    is_selected: bool = True
    color: Optional[str] = None


class UserCalendarCreate(UserCalendarBase):
    """Schema for creating a new user calendar."""
    user_id: uuid.UUID


class UserCalendarUpdate(BaseModel):
    """Schema for updating a user calendar."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_selected: Optional[bool] = None
    color: Optional[str] = None


class UserCalendarResponse(UserCalendarBase):
    """Schema for user calendar API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
