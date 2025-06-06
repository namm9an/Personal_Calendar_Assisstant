"""MongoDB models for the Personal Calendar Assistant (Pydantic v2 compatible)."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId class for Pydantic v2 models."""
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = handler(core_schema)
        schema.update(type="string")
        return schema

class MongoBaseModel(BaseModel):
    """Base model for MongoDB documents."""
    id: Optional[str] = Field(alias="_id", default=None)

    model_config = {
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

class User(MongoBaseModel):
    """User model for MongoDB."""
    email: EmailStr
    name: str
    timezone: str = "UTC"
    working_hours_start: str = "09:00"
    working_hours_end: str = "17:00"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    preferences: Dict[str, Any] = Field(default_factory=dict)

class Event(MongoBaseModel):
    """Event model for MongoDB."""
    summary: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = "UTC"
    location: Optional[str] = None
    attendees: List[EmailStr] = Field(default_factory=list)
    created_by: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "confirmed"
    recurrence: Optional[Dict[str, Any]] = None
    reminders: List[Dict[str, Any]] = Field(default_factory=list)

class Session(MongoBaseModel):
    """Session model for MongoDB."""
    user_id: str
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    scope: List[str] = Field(default_factory=list)

class AgentLog(MongoBaseModel):
    """Agent interaction log model for MongoDB."""
    user_id: str
    session_id: str
    interaction_id: str
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: float
    success: bool = True
    error_message: Optional[str] = None 