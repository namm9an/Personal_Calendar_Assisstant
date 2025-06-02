from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
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
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

class User(MongoBaseModel):
    email: EmailStr
    name: str
    timezone: str = "UTC"
    google_token: Optional[Dict[str, Any]] = None
    microsoft_token: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Event(MongoBaseModel):
    user_id: PyObjectId
    provider: str  # "google" or "microsoft"
    provider_event_id: str
    summary: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None
    attendees: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Session(MongoBaseModel):
    user_id: PyObjectId
    provider: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentLog(MongoBaseModel):
    user_id: PyObjectId
    intent: str
    input_text: str
    steps: List[Dict[str, Any]]
    final_output: str
    created_at: datetime = Field(default_factory=datetime.utcnow) 