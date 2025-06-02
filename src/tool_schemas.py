from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime

class AttendeeSchema(BaseModel):
    email: EmailStr

class EventSchema(BaseModel):
    id: str
    summary: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[AttendeeSchema]] = None

class ListEventsInput(BaseModel):
    provider: str
    user_id: str
    start: datetime
    end: datetime

class ListEventsOutput(BaseModel):
    events: List[EventSchema]

class FreeSlotsInput(BaseModel):
    provider: str
    user_id: str
    duration_minutes: int
    range_start: datetime
    range_end: datetime

    @validator('duration_minutes')
    def duration_positive(cls, v):
        if v <= 0:
            raise ValueError('duration_minutes must be positive')
        return v

class FreeSlotSchema(BaseModel):
    start: datetime
    end: datetime

class FreeSlotsOutput(BaseModel):
    slots: List[FreeSlotSchema]

class CreateEventInput(BaseModel):
    provider: str
    user_id: str
    summary: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[AttendeeSchema]] = None

class CreateEventOutput(BaseModel):
    event: EventSchema

class RescheduleEventInput(BaseModel):
    provider: str
    user_id: str
    event_id: str
    new_start: datetime

class RescheduleEventOutput(BaseModel):
    event: EventSchema

class CancelEventInput(BaseModel):
    provider: str
    user_id: str
    event_id: str

class CancelEventOutput(BaseModel):
    success: bool 