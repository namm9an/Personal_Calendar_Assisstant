from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
from uuid import UUID

class AttendeeSchema(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    response_status: Optional[str] = Field("needsAction", description="Attendee's response status.") # Added from old wrapper
    # Add other relevant attendee fields if necessary

    model_config = {"from_attributes": True}

# Defines the structure of an event for tool outputs
class EventSchema(BaseModel):
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str # ISO datetime string e.g., "2024-01-01T10:00:00Z" or "2024-01-01T10:00:00+05:30"
    end_time: str   # ISO datetime string
    time_zone: Optional[str] = None # e.g., "America/New_York"
    attendees: Optional[List[AttendeeSchema]] = []
    html_link: Optional[str] = None
    calendar_id: str = Field("primary", description="The calendar ID where the event resides.")
    conference_data: Optional[Dict[str, Any]] = Field(None, description="Conference details if any.")
    # raw_response: Optional[Dict[str, Any]] = Field(None, description="Original raw response from the calendar service.") # Optional, for debugging
    status: Optional[str] = Field(None, description="Status of the event, e.g., 'confirmed', 'cancelled'.") # Added common field
    organizer: Optional[AttendeeSchema] = Field(None, description="The organizer of the event.") # Added common field
    creator: Optional[AttendeeSchema] = Field(None, description="The creator of the event.") # Added common field

    model_config = {"from_attributes": True, "extra": 'ignore'}

class ListEventsOutput(BaseModel):
    events: List[EventSchema]

    model_config = {"from_attributes": True}

class TimeSlotSchema(BaseModel):
    """Represents a time slot for availability."""
    start: datetime
    end: datetime
    conflicting_events: Optional[List[str]] = None  # Names of any events that might conflict
    
    model_config = {"from_attributes": True}

class FreeSlotsInput(BaseModel):
    """Input for the find_free_slots tool."""
    
    duration_minutes: int = Field(..., description="Duration of the meeting in minutes.")
    start_date: str = Field(..., description="Start date to search from (format: YYYY-MM-DD).")
    end_date: Optional[str] = Field(
        None, 
        description="End date to search until (format: YYYY-MM-DD). Defaults to start_date + 1 day."
    )
    start_working_hour: Optional[str] = Field(
        None,
        description="Earliest time of day to consider (format: HH:MM, 24-hour). Defaults to user's working hours start."
    )
    end_working_hour: Optional[str] = Field(
        None,
        description="Latest time of day to consider (format: HH:MM, 24-hour). Defaults to user's working hours end."
    )
    attendees: Optional[List[str]] = Field(
        None,
        description="List of attendee emails to check availability for."
    )
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID to check availability in."
    )
    time_zone: Optional[str] = Field(
        None, description="Time zone for the returned slots. Defaults to user's time zone."
    )
    
    model_config = {"from_attributes": True}

class FreeSlotsOutput(BaseModel):
    """Output for the find_free_slots tool."""
    
    available_slots: List[TimeSlotSchema] = Field(..., description="List of available time slots.")
    start_date: str = Field(..., description="Start date of the search period.")
    end_date: str = Field(..., description="End date of the search period.")
    duration_minutes: int = Field(..., description="Requested duration in minutes.")
    working_hours: Optional[Dict[str, str]] = Field(
        None, 
        description="Working hours used for the search (e.g., {'start': '09:00', 'end': '17:00'})."
    )
    time_zone: str = Field(..., description="Time zone used for the results.")
    message: Optional[str] = Field(None, description="Additional information or notes about the results.")
    
    model_config = {"from_attributes": True}

# --- CreateEvent ---
class CreateEventInput(BaseModel):
    """Input for the create_event tool."""
    
    provider: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use")
    user_id: UUID = Field(..., description="ID of the user creating the event")
    summary: str = Field(..., description="Title/summary of the event")
    start: datetime = Field(..., description="Start time of the event")
    end: datetime = Field(..., description="End time of the event")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    attendees: Optional[List[AttendeeSchema]] = Field([], description="List of attendees")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID to create the event in")
    
    @field_validator('end')
    @classmethod
    def end_must_be_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('End time must be after start time')
        return v
    
    @field_validator('summary')
    @classmethod
    def summary_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Summary cannot be empty')
        return v
    
    model_config = {"from_attributes": True}

class CreateEventOutput(BaseModel):
    """Output for the create_event tool."""
    
    event: EventSchema = Field(..., description="The created event")
    
    model_config = {"from_attributes": True}

# --- RescheduleEvent ---
class RescheduleEventInput(BaseModel):
    """Input for the reschedule_event tool."""
    
    provider_name: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use. Renamed from 'provider'.")
    event_id: str = Field(..., description="ID of the event to reschedule")
    new_start_datetime: datetime = Field(..., description="New start date and time for the event. Renamed from 'new_start'.")
    new_end_datetime: datetime = Field(..., description="New end date and time for the event.")
    new_time_zone: Optional[str] = Field(None, description="Optional new time zone for the event (e.g., 'America/New_York'). If None, existing or user's default may be used.")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")
    
    @field_validator('event_id')
    @classmethod
    def event_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Event ID cannot be empty')
        return v

    @field_validator('new_end_datetime')
    @classmethod
    def end_must_be_after_start(cls, v, values):
        if 'new_start_datetime' in values and v <= values['new_start_datetime']:
            raise ValueError('New end time must be after new start time')
        return v
    
    model_config = {"from_attributes": True}

class RescheduleEventOutput(BaseModel):
    """Output for the reschedule_event tool."""
    
    event: EventSchema = Field(..., description="The updated event")
    
    model_config = {"from_attributes": True}

# --- CancelEvent ---
class CancelEventInput(BaseModel):
    """Input for the cancel_event tool."""
    
    provider: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use")
    user_id: UUID = Field(..., description="ID of the user who owns the event")
    event_id: str = Field(..., description="ID of the event to cancel")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")
    
    @field_validator('event_id')
    @classmethod
    def event_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Event ID cannot be empty')
        return v
    
    model_config = {"from_attributes": True}

class CancelEventOutput(BaseModel):
    """Output for the cancel_event tool."""
    
    success: bool = Field(..., description="True if the event was successfully cancelled")
    message: Optional[str] = Field(None, description="Additional information about the cancellation")
    
    model_config = {"from_attributes": True}

# We will add other Input/Output schemas here later
# e.g., ListEventsInput, etc.

# Alias for backward compatibility and test code that uses FreeSlotSchema
FreeSlotSchema = TimeSlotSchema
