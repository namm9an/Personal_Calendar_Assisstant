from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from pydantic import BaseModel
from src.db.connection import mongodb
from src.models.mongodb_models import User, Event, Session, AgentLog
from src.core.exceptions import (
    DatabaseError,
    ValidationError,
    NotFoundError
)

T = TypeVar('T', bound=BaseModel)

class MongoDBRepository(Generic[T]):
    """Base repository for MongoDB operations."""
    
    def __init__(self, collection_name: str, model_class: type[T]):
        self.collection_name = collection_name
        self.model_class = model_class
        self._db: Optional[AsyncIOMotorDatabase] = None

    @property
    async def db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._db is None:
            self._db = await mongodb.get_database()
        return self._db

    @property
    async def collection(self):
        """Get collection instance."""
        db = await self.db
        return db[self.collection_name]

    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new document."""
        try:
            # Add timestamps
            now = datetime.utcnow()
            data.update({
                "created_at": now,
                "updated_at": now
            })
            
            # Insert document
            result = await (await self.collection).insert_one(data)
            
            # Fetch and return created document
            created = await (await self.collection).find_one({"_id": result.inserted_id})
            if not created:
                raise DatabaseError("Failed to create document")
                
            return self.model_class(**created)
            
        except Exception as e:
            raise DatabaseError(f"Failed to create document: {str(e)}")

    async def get_by_id(self, id: str) -> T:
        """Get document by ID."""
        try:
            document = await (await self.collection).find_one({"_id": id})
            if not document:
                raise NotFoundError(f"Document with id {id} not found")
            return self.model_class(**document)
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get document: {str(e)}")

    async def get_one(self, filter: Dict[str, Any]) -> T:
        """Get one document matching filter."""
        try:
            document = await (await self.collection).find_one(filter)
            if not document:
                raise NotFoundError(f"No document found matching filter: {filter}")
            return self.model_class(**document)
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get document: {str(e)}")

    async def get_many(
        self,
        filter: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """Get multiple documents matching filter."""
        try:
            cursor = (await self.collection).find(filter)
            
            if sort:
                cursor = cursor.sort(sort)
                
            cursor = cursor.skip(skip).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            return [self.model_class(**doc) for doc in documents]
            
        except Exception as e:
            raise DatabaseError(f"Failed to get documents: {str(e)}")

    async def update(
        self,
        id: str,
        data: Dict[str, Any],
        upsert: bool = False
    ) -> T:
        """Update document by ID."""
        try:
            # Add updated timestamp
            data["updated_at"] = datetime.utcnow()
            
            # Update document
            result = await (await self.collection).update_one(
                {"_id": id},
                {"$set": data},
                upsert=upsert
            )
            
            if not result.modified_count and not upsert:
                raise NotFoundError(f"Document with id {id} not found")
                
            # Fetch and return updated document
            updated = await (await self.collection).find_one({"_id": id})
            if not updated:
                raise DatabaseError("Failed to update document")
                
            return self.model_class(**updated)
            
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update document: {str(e)}")

    async def delete(self, id: str) -> bool:
        """Delete document by ID."""
        try:
            result = await (await self.collection).delete_one({"_id": id})
            if not result.deleted_count:
                raise NotFoundError(f"Document with id {id} not found")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete document: {str(e)}")

    async def count(self, filter: Dict[str, Any]) -> int:
        """Count documents matching filter."""
        try:
            return await (await self.collection).count_documents(filter)
        except Exception as e:
            raise DatabaseError(f"Failed to count documents: {str(e)}")

    async def exists(self, filter: Dict[str, Any]) -> bool:
        """Check if document exists matching filter."""
        try:
            return await (await self.collection).count_documents(filter) > 0
        except Exception as e:
            raise DatabaseError(f"Failed to check document existence: {str(e)}")

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        try:
            cursor = (await self.collection).aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            raise DatabaseError(f"Failed to run aggregation: {str(e)}")

class MongoRepository:
    def __init__(self, client: AsyncIOMotorClient):
        self.client = client
        self.db = client.get_database("calendar_db")
        self.users = self.db.users
        self.events = self.db.events
    
    async def initialize(self):
        """Initialize repository (create indexes, etc.)."""
        await self.users.create_index("email", unique=True)
        await self.events.create_index([("user_id", 1), ("provider", 1)])
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        result = await self.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        return await self.users.find_one({"email": email})
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return await self.users.find_one({"_id": ObjectId(user_id)})
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )
        return result
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        result = await self.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event."""
        event_data["created_at"] = datetime.utcnow()
        event_data["updated_at"] = datetime.utcnow()
        result = await self.events.insert_one(event_data)
        event_data["_id"] = result.inserted_id
        return event_data
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event by ID."""
        return await self.events.find_one({"_id": ObjectId(event_id)})
    
    async def get_user_events(self, user_id: str, provider: str) -> List[Dict[str, Any]]:
        """Get all events for a user from a specific provider."""
        cursor = self.events.find({"user_id": user_id, "provider": provider})
        return await cursor.to_list(length=None)
    
    async def update_event(self, event_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update event data."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.events.find_one_and_update(
            {"_id": ObjectId(event_id)},
            {"$set": update_data},
            return_document=True
        )
        return result
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        result = await self.events.delete_one({"_id": ObjectId(event_id)})
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