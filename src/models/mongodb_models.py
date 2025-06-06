from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator, HttpUrl, field_validator
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        json_schema = handler(core_schema)
        json_schema.update(type="string")
        return json_schema

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class Attendee(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    response_status: Optional[str] = Field(default="needsAction")

    @field_validator("response_status")
    def validate_response_status(cls, v):
        valid_statuses = ["accepted", "declined", "tentative", "needsAction"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid response status. Must be one of {valid_statuses}")
        return v

class Event(MongoBaseModel):
    user_id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start: datetime
    end: datetime
    attendees: List[Attendee] = Field(default_factory=list)
    html_link: Optional[HttpUrl] = None
    provider: str = Field(..., description="Calendar provider (google/microsoft)")
    provider_event_id: Optional[str] = None
    recurring_event_id: Optional[str] = None
    status: str = Field(default="confirmed")
    color_id: Optional[str] = None
    reminders: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("provider")
    def validate_provider(cls, v):
        valid_providers = ["google", "microsoft"]
        if v not in valid_providers:
            raise ValueError(f"Invalid provider. Must be one of {valid_providers}")
        return v

    @field_validator("status")
    def validate_status(cls, v):
        valid_statuses = ["confirmed", "tentative", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
        return v

    @field_validator("end")
    def validate_end_after_start(cls, v, values):
        if "start" in values and v <= values["start"]:
            raise ValueError("End time must be after start time")
        return v

class User(MongoBaseModel):
    email: EmailStr
    name: Optional[str] = None
    is_active: bool = Field(default=True)
    timezone: str = Field(default="UTC")
    working_hours_start: str = Field(default="09:00")
    working_hours_end: str = Field(default="17:00")
    
    # Google Calendar
    google_id: Optional[str] = None
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    
    # Microsoft Calendar
    microsoft_id: Optional[str] = None
    microsoft_access_token: Optional[str] = None
    microsoft_refresh_token: Optional[str] = None
    microsoft_token_expiry: Optional[datetime] = None
    
    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("timezone")
    def validate_timezone(cls, v):
        try:
            import pytz
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}")

    @field_validator("working_hours_start", "working_hours_end")
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM format")

class Session(MongoBaseModel):
    user_id: str
    token: str
    expires_at: datetime
    provider: str = Field(..., description="Auth provider (google/microsoft)")
    refresh_token: Optional[str] = None
    is_active: bool = Field(default=True)

    @field_validator("provider")
    def validate_provider(cls, v):
        valid_providers = ["google", "microsoft"]
        if v not in valid_providers:
            raise ValueError(f"Invalid provider. Must be one of {valid_providers}")
        return v

class AgentLog(MongoBaseModel):
    user_id: str
    action: str
    input_text: str
    output_text: Optional[str] = None
    status: str = Field(default="success")
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None

    @field_validator("status")
    def validate_status(cls, v):
        valid_statuses = ["success", "error", "in_progress"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
        return v 