"""
Microsoft Calendar schemas for the Personal Calendar Assistant.
"""
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator, field_validator


class MSAttendee(BaseModel):
    """Schema for an event attendee."""
    email: str = Field(..., description="Email address of the attendee")
    name: Optional[str] = Field(None, description="Display name of the attendee")


class MSTimeSlot(BaseModel):
    """Schema for a time slot."""
    start: datetime = Field(..., description="Start time of the slot")
    end: datetime = Field(..., description="End time of the slot")
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSTimeSlot':
        """Validate that end is after start."""
        if self.start >= self.end:
            raise ValueError("End time must be after start time")
        return self


class MSCalendarEventBase(BaseModel):
    """Base fields for calendar event schemas."""
    summary: str = Field(..., description="Event title or summary")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    start: datetime = Field(..., description="Event start time")
    end: datetime = Field(..., description="Event end time")
    is_all_day: Optional[bool] = Field(False, description="Whether the event is an all-day event")
    attendees: Optional[List[Dict[str, str]]] = Field(None, description="List of event attendees")
    
    @field_validator('start', 'end')
    @classmethod
    def validate_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime has timezone info."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class MSCalendarCreate(MSCalendarEventBase):
    """Schema for creating a new calendar event."""
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSCalendarCreate':
        """Validate that end is after start."""
        if self.start >= self.end:
            raise ValueError("End time must be after start time")
        return self


class MSCalendarUpdate(BaseModel):
    """Schema for updating an existing calendar event."""
    summary: Optional[str] = Field(None, description="Event title or summary")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    start: Optional[datetime] = Field(None, description="Event start time")
    end: Optional[datetime] = Field(None, description="Event end time")
    is_all_day: Optional[bool] = Field(None, description="Whether the event is an all-day event")
    attendees: Optional[List[Dict[str, str]]] = Field(None, description="List of event attendees")
    
    @field_validator('start', 'end')
    @classmethod
    def validate_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime has timezone info."""
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSCalendarUpdate':
        """Validate that end is after start if both are provided."""
        if self.start and self.end and self.start >= self.end:
            raise ValueError("End time must be after start time")
        return self


class MSCalendarEvent(MSCalendarEventBase):
    """Schema for calendar event responses."""
    id: str = Field(..., description="Event ID")
    organizer: Optional[Dict[str, str]] = Field(None, description="Event organizer details")
    created: Optional[datetime] = Field(None, description="Event creation time")
    updated: Optional[datetime] = Field(None, description="Event last update time")
    status: Optional[str] = Field(None, description="Event status")
    recurrence: Optional[Any] = Field(None, description="Event recurrence pattern")
    web_link: Optional[str] = Field(None, description="Event web link")
    
    @field_validator('created', 'updated')
    @classmethod
    def validate_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime has timezone info."""
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    model_config = {"from_attributes": True}


class MSFreeSlotRequest(BaseModel):
    """Schema for requesting free time slots."""
    duration_minutes: int = Field(
        ge=5,
        le=480,
        description="Duration of required free slot in minutes (between 5 minutes and 8 hours)"
    )
    start_date: Optional[datetime] = Field(None, description="Start of time range to search")
    end_date: Optional[datetime] = Field(None, description="End of time range to search")
    attendees: Optional[List[str]] = Field(None, description="List of attendee email addresses")
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime has timezone info."""
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'MSFreeSlotRequest':
        """Validate date range if both dates are provided."""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")
        return self


class MSFreeSlotResponse(BaseModel):
    """Schema for free time slot response."""
    slots: List[MSTimeSlot] = Field(..., description="List of available time slots")
    
    model_config = {"from_attributes": True}
