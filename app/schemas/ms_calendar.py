"""
Microsoft Calendar schemas for the Personal Calendar Assistant.
"""
from datetime import datetime, time
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator, field_validator


class MSAttendee(BaseModel):
    """Schema for an event attendee."""
    email: str
    name: Optional[str] = None


class MSTimeSlot(BaseModel):
    """Schema for a time slot."""
    start: datetime
    end: datetime


class MSCalendarEventBase(BaseModel):
    """Base fields for calendar event schemas."""
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start: datetime
    end: datetime
    is_all_day: Optional[bool] = False
    attendees: Optional[List[Dict[str, str]]] = None


class MSCalendarCreate(MSCalendarEventBase):
    """Schema for creating a new calendar event."""
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSCalendarCreate':
        """Validate that end is after start."""
        if self.start and self.end and self.start >= self.end:
            raise ValueError("End time must be after start time")
        return self


class MSCalendarUpdate(BaseModel):
    """Schema for updating an existing calendar event."""
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    attendees: Optional[List[Dict[str, str]]] = None
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSCalendarUpdate':
        """Validate that end is after start if both are provided."""
        if self.start and self.end and self.start >= self.end:
            raise ValueError("End time must be after start time")
        return self


class MSCalendarEvent(MSCalendarEventBase):
    """Schema for calendar event responses."""
    id: str
    organizer: Optional[Dict[str, str]] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    status: Optional[str] = None
    recurrence: Optional[Any] = None
    web_link: Optional[str] = None
    
    model_config = {"from_attributes": True}


class MSFreeSlotRequest(BaseModel):
    """Schema for requesting free time slots."""
    duration_minutes: int = Field(ge=5, le=480)  # Between 5 minutes and 8 hours
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    attendees: Optional[List[str]] = None
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSFreeSlotRequest':
        """Validate date range if both dates are provided."""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")
        return self


class MSFreeSlotResponse(BaseModel):
    """Schema for free time slot response."""
    slots: List[MSTimeSlot]
    
    model_config = {"from_attributes": True}
