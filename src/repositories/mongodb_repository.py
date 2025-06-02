from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from src.db.connection import mongodb
from src.models.mongodb_models import User, Event, Session, AgentLog

class MongoDBRepository:
    def __init__(self):
        self.db = mongodb.db

    # User operations
    async def create_user(self, user: User) -> User:
        user_dict = user.dict(by_alias=True, exclude={'id'})
        result = await self.db.users.insert_one(user_dict)
        user.id = result.inserted_id
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        user_dict = await self.db.users.find_one({"email": email})
        if user_dict:
            return User(**user_dict)
        return None

    async def update_user_tokens(self, user_id: ObjectId, provider: str, tokens: Dict[str, Any]) -> bool:
        result = await self.db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    f"{provider}_token": tokens,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    # Event operations
    async def create_event(self, event: Event) -> Event:
        event_dict = event.dict(by_alias=True, exclude={'id'})
        result = await self.db.events.insert_one(event_dict)
        event.id = result.inserted_id
        return event

    async def get_user_events(self, user_id: ObjectId, start: datetime, end: datetime) -> List[Event]:
        cursor = self.db.events.find({
            "user_id": user_id,
            "start": {"$gte": start},
            "end": {"$lte": end}
        })
        events = await cursor.to_list(length=None)
        return [Event(**event) for event in events]

    async def get_event_by_provider_id(self, user_id: ObjectId, provider: str, provider_event_id: str) -> Optional[Event]:
        event_dict = await self.db.events.find_one({
            "user_id": user_id,
            "provider": provider,
            "provider_event_id": provider_event_id
        })
        if event_dict:
            return Event(**event_dict)
        return None

    async def update_event(self, event_id: ObjectId, update_data: Dict[str, Any]) -> bool:
        update_data["updated_at"] = datetime.utcnow()
        result = await self.db.events.update_one(
            {"_id": event_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_event(self, event_id: ObjectId) -> bool:
        result = await self.db.events.delete_one({"_id": event_id})
        return result.deleted_count > 0

    # Session operations
    async def create_session(self, session: Session) -> Session:
        session_dict = session.dict(by_alias=True, exclude={'id'})
        result = await self.db.sessions.insert_one(session_dict)
        session.id = result.inserted_id
        return session

    async def get_active_session(self, user_id: ObjectId, provider: str) -> Optional[Session]:
        session_dict = await self.db.sessions.find_one({
            "user_id": user_id,
            "provider": provider,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if session_dict:
            return Session(**session_dict)
        return None

    # Agent log operations
    async def create_agent_log(self, log: AgentLog) -> AgentLog:
        log_dict = log.dict(by_alias=True, exclude={'id'})
        result = await self.db.agent_logs.insert_one(log_dict)
        log.id = result.inserted_id
        return log

    async def get_user_agent_logs(self, user_id: ObjectId, limit: int = 10) -> List[AgentLog]:
        cursor = self.db.agent_logs.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        logs = await cursor.to_list(length=None)
        return [AgentLog(**log) for log in logs] 