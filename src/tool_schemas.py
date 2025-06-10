from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import List, Optional
from datetime import datetime

class AttendeeSchema(BaseModel):
    """Schema for event attendees."""
    email: str
    name: Optional[str] = None
    response_status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EventSchema(BaseModel):
    """Schema for calendar events."""
    id: str
    summary: str
    start: str
    end: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: List[AttendeeSchema] = Field(default_factory=list)
    html_link: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EventInput(BaseModel):
    provider: str
    user_id: str
    calendar_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ListEventsInput(EventInput):
    """Input schema for listing events."""
    start: str
    end: str
    max_results: Optional[int] = 10
    model_config = ConfigDict(from_attributes=True)

    @field_validator('start', 'end', mode='before')
    @classmethod
    def convert_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

class ListEventsOutput(BaseModel):
    """Output schema for listing events."""
    events: List[EventSchema]
    model_config = ConfigDict(from_attributes=True)

class FreeSlotSchema(BaseModel):
    """Schema for free time slots."""
    start: str
    end: str
    model_config = ConfigDict(from_attributes=True)

class FreeSlotsInput(EventInput):
    """Input schema for finding free slots."""
    duration_minutes: int
    range_start: str
    range_end: str
    model_config = ConfigDict(from_attributes=True)

    @field_validator('range_start', 'range_end', mode='before')
    @classmethod
    def convert_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, value):
        if value <= 0:
            raise ValueError("Duration must be positive")
        return value

class FreeSlotsOutput(BaseModel):
    """Output schema for finding free slots."""
    slots: List[FreeSlotSchema]
    model_config = ConfigDict(from_attributes=True)

class CreateEventInput(BaseModel):
    """Input schema for creating events."""
    provider: str
    user_id: str
    summary: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: List[AttendeeSchema] = Field(default_factory=list)
    calendar_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class CreateEventOutput(BaseModel):
    """Output schema for creating events."""
    event: EventSchema
    status: str = "success"
    model_config = ConfigDict(from_attributes=True)

class RescheduleEventInput(BaseModel):
    """Input schema for rescheduling events."""
    provider: str
    user_id: str
    event_id: str
    new_start: datetime
    new_end: datetime
    calendar_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("new_start", "new_end", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class RescheduleEventOutput(BaseModel):
    """Output schema for rescheduling events."""
    event: EventSchema
    status: str = "success"
    model_config = ConfigDict(from_attributes=True)

class CancelEventInput(BaseModel):
    """Input schema for canceling events."""
    provider: str
    user_id: str
    event_id: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    calendar_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class CancelEventOutput(BaseModel):
    """Output schema for canceling events."""
    success: bool = True
    status: str = "success"
    model_config = ConfigDict(from_attributes=True)

class DeleteEventInput(BaseModel):
    """Input schema for deleting events."""
    provider: str
    user_id: str
    event_id: str
    calendar_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UpdateEventInput(BaseModel):
    """Input schema for updating events."""
    provider: str
    user_id: str
    event_id: str
    summary: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[AttendeeSchema]] = Field(default_factory=list)
    calendar_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class UpdateEventOutput(BaseModel):
    """Output schema for updating events."""
    event: EventSchema
    status: str = "success"
    model_config = ConfigDict(from_attributes=True)

class FindFreeSlotsInput(BaseModel):
    provider: str
    user_id: str
    range_start: datetime
    range_end: datetime
    duration_minutes: int
    calendar_id: Optional[str] = None

    @field_validator("range_start", "range_end", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, value):
        if value <= 0:
            raise ValueError("Duration must be positive")
        return value

class DeleteEventOutput(BaseModel):
    success: bool

# Add other models as needed, following the same pattern. 