from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.tool_schemas import EventSchema, AttendeeSchema

class CalendarService(ABC):
    """Abstract base class for calendar services."""
    
    @abstractmethod
    async def create(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Create a new calendar event."""
        pass

    @abstractmethod
    async def list(
        self,
        start: datetime,
        end: datetime,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """List calendar events within a time range."""
        pass

    @abstractmethod
    async def update(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Update an existing calendar event."""
        pass

    @abstractmethod
    async def delete(self, event_id: str) -> None:
        """Delete a calendar event."""
        pass

    @abstractmethod
    async def get_free_slots(
        self,
        start: datetime,
        end: datetime,
        duration_minutes: int
    ) -> List[Dict[str, datetime]]:
        """Get free time slots within a time range."""
        pass 