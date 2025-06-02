"""
Base class for calendar tools to ensure consistent interface across all implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.tool_schemas import (
    EventSchema, FreeSlotSchema, ListEventsOutput, FreeSlotsOutput,
    CreateEventOutput, RescheduleEventOutput, CancelEventOutput
)

class CalendarToolBase(ABC):
    """Base class for all calendar tools
    
    This ensures a consistent interface across all calendar tool implementations,
    making them easy to test and maintain.
    """
    
    def __init__(self, db_session: Session, user_id: str = None, user: User = None):
        """Initialize the tool with database session and user information
        
        Args:
            db_session: SQLAlchemy database session
            user_id: User ID string (UUID) - optional if user is provided
            user: User model instance - optional if user_id is provided
        """
        self.db_session = db_session
        self._user = user
        self._user_id = user_id
        
    @property
    def user(self) -> User:
        """Get the user model instance, fetching from DB if needed"""
        if self._user is None and self._user_id:
            from app.models.user import User
            self._user = self.db_session.query(User).filter(User.id == self._user_id).first()
        return self._user
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given input data
        
        Args:
            input_data: Dictionary of input parameters
            
        Returns:
            Dictionary of output results
        """
        pass


class ListEventsTool(CalendarToolBase):
    """Tool for listing calendar events"""
    
    def execute(self, input_data: Dict[str, Any]) -> ListEventsOutput:
        """Execute the list events tool with given input data"""
        from app.agent.calendar_tool_wrappers import list_events_tool
        # Convert input_data dict to appropriate input type if needed
        return list_events_tool(self.db_session, **input_data)


class FindFreeSlotsTool(CalendarToolBase):
    """Tool for finding free time slots"""
    
    def execute(self, input_data: Dict[str, Any]) -> FreeSlotsOutput:
        """Execute the find free slots tool with given input data"""
        from app.agent.calendar_tool_wrappers import find_free_slots_tool
        # Create CalendarTools instance from the old API
        from app.agent.tools import CalendarTools
        calendar_tools = CalendarTools(self.user, self.db_session)
        return find_free_slots_tool(calendar_tools, input_data)


class CreateEventTool(CalendarToolBase):
    """Tool for creating calendar events"""
    
    def execute(self, input_data: Dict[str, Any]) -> CreateEventOutput:
        """Execute the create event tool with given input data"""
        from app.agent.calendar_tool_wrappers import create_event_tool
        # Create CalendarTools instance from the old API
        from app.agent.tools import CalendarTools
        calendar_tools = CalendarTools(self.user, self.db_session)
        return create_event_tool(calendar_tools, input_data)


class RescheduleEventTool(CalendarToolBase):
    """Tool for rescheduling calendar events"""
    
    def execute(self, input_data: Dict[str, Any]) -> RescheduleEventOutput:
        """Execute the reschedule event tool with given input data"""
        from app.agent.calendar_tool_wrappers import reschedule_event_tool
        # Create CalendarTools instance from the old API
        from app.agent.tools import CalendarTools
        calendar_tools = CalendarTools(self.user, self.db_session)
        return reschedule_event_tool(calendar_tools, input_data)


class CancelEventTool(CalendarToolBase):
    """Tool for canceling calendar events"""
    
    def execute(self, input_data: Dict[str, Any]) -> CancelEventOutput:
        """Execute the cancel event tool with given input data"""
        from app.agent.calendar_tool_wrappers import cancel_event_tool
        # Create CalendarTools instance from the old API
        from app.agent.tools import CalendarTools
        calendar_tools = CalendarTools(self.user, self.db_session)
        return cancel_event_tool(calendar_tools, input_data)
