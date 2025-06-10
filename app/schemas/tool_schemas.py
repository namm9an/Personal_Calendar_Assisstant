from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime, timedelta
from uuid import UUID

class AttendeeSchema(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    response_status: Optional[str] = Field("needsAction", description="Attendee's response status.")
    
    model_config = {"from_attributes": True}

# Defines the structure of an event for tool outputs
class EventSchema(BaseModel):
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str  # ISO datetime string
    end_time: str    # ISO datetime string
    time_zone: Optional[str] = None
    attendees: Optional[List[AttendeeSchema]] = []
    html_link: Optional[str] = None
    calendar_id: str = Field("primary", description="The calendar ID where the event resides.")
    conference_data: Optional[Dict[str, Any]] = Field(None, description="Conference details if any.")
    status: Optional[str] = Field(None, description="Status of the event, e.g., 'confirmed', 'cancelled'.")
    organizer: Optional[AttendeeSchema] = Field(None, description="The organizer of the event.")
    creator: Optional[AttendeeSchema] = Field(None, description="The creator of the event.")

    model_config = {"from_attributes": True, "extra": 'ignore'}

class ListEventsOutput(BaseModel):
    events: List[EventSchema]
    model_config = {"from_attributes": True}

class TimeSlotSchema(BaseModel):
    """Represents a time slot for availability."""
    start: str  # ISO datetime string
    end: str    # ISO datetime string
    conflicting_events: Optional[List[str]] = None  # Names of any events that might conflict
    
    model_config = {"from_attributes": True}

class FreeSlotsInput(BaseModel):
    """Input for the find_free_slots tool."""
    
    provider: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use")
    user_id: UUID = Field(..., description="ID of the user finding free slots")
    duration_minutes: int = Field(..., description="Duration of the free slot in minutes")
    range_start: str = Field(..., description="Start of the range to search for free slots (format: ISO 8601)")
    range_end: str = Field(..., description="End of the range to search for free slots (format: ISO 8601)")
    start_working_hour: Optional[str] = Field(None, description="Start of working hours (format: HH:MM)")
    end_working_hour: Optional[str] = Field(None, description="End of working hours (format: HH:MM)")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID to search for free slots in")
    
    @field_validator('range_start')
    @classmethod
    def validate_range_start(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('range_start must be in ISO 8601 format')
    
    @field_validator('range_end')
    @classmethod
    def validate_range_end(cls, v, values):
        if isinstance(v, datetime):
            v = v.isoformat()
        try:
            v_dt = datetime.fromisoformat(v)
            if hasattr(values, 'data') and 'range_start' in values.data:
                start = values.data['range_start']
                if isinstance(start, datetime):
                    start = start.isoformat()
                start_dt = datetime.fromisoformat(start)
                if v_dt <= start_dt:
                    raise ValueError('End time must be after start time')
            return v
        except ValueError:
            raise ValueError('range_end must be in ISO 8601 format')
    
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
    start: str = Field(..., description="Start time of the event (format: ISO 8601)")
    end: str = Field(..., description="End time of the event (format: ISO 8601)")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    attendees: Optional[List[AttendeeSchema]] = Field([], description="List of attendees")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID to create the event in")
    
    @field_validator('start')
    @classmethod
    def validate_start(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('start must be in ISO 8601 format')
    
    @field_validator('end')
    @classmethod
    def validate_end(cls, v, values):
        if isinstance(v, datetime):
            v = v.isoformat()
        try:
            v_dt = datetime.fromisoformat(v)
            if hasattr(values, 'data') and 'start' in values.data:
                start = values.data['start']
                if isinstance(start, datetime):
                    start = start.isoformat()
                start_dt = datetime.fromisoformat(start)
                if v_dt <= start_dt:
                    raise ValueError('End time must be after start time')
            return v
        except ValueError:
            raise ValueError('end must be in ISO 8601 format')
    
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
    
    provider: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use")
    user_id: UUID = Field(..., description="ID of the user rescheduling the event")
    event_id: str = Field(..., description="ID of the event to reschedule")
    new_start: str = Field(..., description="New start time (format: ISO 8601)")
    new_end: Optional[str] = Field(None, description="New end time (format: ISO 8601)")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")
    
    @field_validator('new_start')
    @classmethod
    def validate_new_start(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('new_start must be in ISO 8601 format')
    
    @field_validator('new_end')
    @classmethod
    def validate_new_end(cls, v, values):
        if v is None:
            return v
        if isinstance(v, datetime):
            v = v.isoformat()
        try:
            v_dt = datetime.fromisoformat(v)
            if hasattr(values, 'data') and 'new_start' in values.data:
                start = values.data['new_start']
                if isinstance(start, datetime):
                    start = start.isoformat()
                start_dt = datetime.fromisoformat(start)
                if v_dt <= start_dt:
                    raise ValueError('New end time must be after new start time')
            return v
        except ValueError:
            raise ValueError('new_end must be in ISO 8601 format')
    
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

class ListEventsInput(BaseModel):
    """Input for the list_events tool."""
    
    provider: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use")
    user_id: UUID = Field(..., description="ID of the user listing events")
    start: str = Field(..., description="Start date to list events from (format: ISO 8601)")
    end: Optional[str] = Field(None, description="End date to list events until (format: ISO 8601). Defaults to start + 1 day.")
    calendar_id: Optional[str] = Field("primary", description="Calendar ID to list events from.")
    
    @field_validator('start')
    @classmethod
    def validate_start(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('start must be in ISO 8601 format')
    
    @field_validator('end')
    @classmethod
    def validate_end(cls, v, values):
        if v is None:
            if hasattr(values, 'data') and 'start' in values.data:
                start = values.data['start']
                if isinstance(start, datetime):
                    start = start.isoformat()
                start_dt = datetime.fromisoformat(start)
                return (start_dt + timedelta(days=1)).isoformat()
            return None
        if isinstance(v, datetime):
            v = v.isoformat()
        try:
            v_dt = datetime.fromisoformat(v)
            if hasattr(values, 'data') and 'start' in values.data:
                start = values.data['start']
                if isinstance(start, datetime):
                    start = start.isoformat()
                start_dt = datetime.fromisoformat(start)
                if v_dt <= start_dt:
                    raise ValueError('End time must be after start time')
            return v
        except ValueError:
            raise ValueError('end must be in ISO 8601 format')
    
    model_config = {"from_attributes": True}

class DeleteEventInput(BaseModel):
    """Input schema for deleting an event."""
    event_id: str = Field(..., description="ID of the event to delete")
    calendar_id: Optional[str] = Field("primary", description="ID of the calendar containing the event")
    user_id: Optional[str] = Field(None, description="ID of the user who owns the event")
