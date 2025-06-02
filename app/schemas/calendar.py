"""
Pydantic schemas for calendar events.
"""
from datetime import datetime, time
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class EventStatus(str, Enum):
    """Event status enum."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventAttendee(BaseModel):
    """Event attendee schema."""
    email: str
    name: Optional[str] = None
    response_status: Optional[str] = None


class TimeSlot(BaseModel):
    """Time slot with start and end times."""
    start: datetime
    end: datetime
    
    @field_validator('end')
    @classmethod
    def end_after_start(cls, v, values):
        """Validate that end time is after start time."""
        if 'start' in values and v <= values['start']:
            raise ValueError('end time must be after start time')
        return v


class EventBase(BaseModel):
    """Base class for event schemas."""
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    time_slot: TimeSlot
    attendees: Optional[List[EventAttendee]] = None
    status: Optional[EventStatus] = EventStatus.CONFIRMED
    color_id: Optional[str] = None
    

class EventCreate(EventBase):
    """Event creation schema."""
    calendar_id: Optional[str] = "primary"
    time_zone: Optional[str] = None
    send_notifications: bool = False
    reminders: Optional[Dict[str, Any]] = None
    conference_data: Optional[Dict[str, Any]] = None
    
    @field_validator('reminders')
    @classmethod
    def validate_reminders(cls, v):
        """Validate reminders format."""
        if v is not None:
            # Ensure reminders has the correct structure
            if not isinstance(v, dict):
                raise ValueError("reminders must be a dictionary")
            if "useDefault" not in v and "overrides" not in v:
                raise ValueError("reminders must contain useDefault or overrides or both")
        return v


class EventUpdate(BaseModel):
    """Event update schema."""
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    time_slot: Optional[TimeSlot] = None
    attendees: Optional[List[EventAttendee]] = None
    status: Optional[EventStatus] = None
    color_id: Optional[str] = None
    send_notifications: bool = False
    

class Event(EventBase):
    """Event schema."""
    id: str
    calendar_id: str = "primary"
    html_link: Optional[str] = None
    created: datetime
    updated: datetime
    organizer: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}


class WorkingHours(BaseModel):
    """Working hours configuration."""
    monday: Optional[tuple[time, time]] = None
    tuesday: Optional[tuple[time, time]] = None
    wednesday: Optional[tuple[time, time]] = None
    thursday: Optional[tuple[time, time]] = None
    friday: Optional[tuple[time, time]] = None
    saturday: Optional[tuple[time, time]] = None
    sunday: Optional[tuple[time, time]] = None
    time_zone: str = "UTC"


class FreeSlotRequest(BaseModel):
    """Request schema for finding free time slots."""
    duration_minutes: int = Field(..., gt=0, description="Duration of the meeting in minutes")
    start_date: datetime = Field(..., description="Start date for the availability window")
    end_date: datetime = Field(..., description="End date for the availability window") 
    working_hours: Optional[WorkingHours] = None
    attendees: Optional[List[str]] = None
    calendar_ids: Optional[List[str]] = None
    
    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v, values):
        """Validate that end date is after start date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end date must be after start date')
        return v
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, v):
        """Validate that duration is positive."""
        if v <= 0:
            raise ValueError('duration must be greater than 0')
        return v


class FreeSlot(BaseModel):
    """Free time slot schema."""
    start: datetime
    end: datetime


class FreeSlotResponse(BaseModel):
    """Response schema for free time slots."""
    slots: List[FreeSlot]
    time_zone: str
