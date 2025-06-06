from typing import Dict, Any, Optional
from datetime import datetime
from src.calendar_tool_wrappers import (
    list_events_tool,
    find_free_slots_tool,
    create_event_tool,
    update_event_tool,
    delete_event_tool,
    reschedule_event_tool,
    cancel_event_tool
)
from src.tool_schemas import (
    ListEventsInput,
    FindFreeSlotsInput,
    CreateEventInput,
    UpdateEventInput,
    DeleteEventInput,
    RescheduleEventInput,
    CancelEventInput
)
from src.core.exceptions import ToolExecutionError

class CalendarAgent:
    def __init__(self):
        self.supported_providers = ["google", "microsoft"]

    async def run(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Run the calendar agent with the given input."""
        if provider not in self.supported_providers:
            raise ToolExecutionError(f"Unsupported provider: {provider}")

        # Parse the input text to determine the action
        action = self._parse_action(text)
        
        try:
            if action == "list_events":
                return await self._handle_list_events(user_id, provider)
            elif action == "find_free_slots":
                return await self._handle_find_free_slots(text, user_id, provider)
            elif action == "create_event":
                return await self._handle_create_event(text, user_id, provider)
            elif action == "update_event":
                return await self._handle_update_event(text, user_id, provider)
            elif action == "delete_event":
                return await self._handle_delete_event(text, user_id, provider)
            elif action == "reschedule_event":
                return await self._handle_reschedule_event(text, user_id, provider)
            elif action == "cancel_event":
                return await self._handle_cancel_event(text, user_id, provider)
            else:
                raise ToolExecutionError(f"Unknown action: {action}")
        except Exception as e:
            raise ToolExecutionError(f"Failed to execute action: {str(e)}")

    def _parse_action(self, text: str) -> str:
        """Parse the input text to determine the action."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["list", "show", "get", "view"]):
            return "list_events"
        elif any(word in text_lower for word in ["find", "search", "look for"]):
            return "find_free_slots"
        elif any(word in text_lower for word in ["create", "schedule", "book", "add"]):
            return "create_event"
        elif any(word in text_lower for word in ["update", "change", "modify"]):
            return "update_event"
        elif any(word in text_lower for word in ["delete", "remove"]):
            return "delete_event"
        elif any(word in text_lower for word in ["reschedule", "move"]):
            return "reschedule_event"
        elif any(word in text_lower for word in ["cancel"]):
            return "cancel_event"
        else:
            raise ToolExecutionError("Could not determine action from input")

    async def _handle_list_events(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle listing events."""
        input = ListEventsInput(
            provider=provider,
            user_id=user_id
        )
        events = await list_events_tool(input)
        return {"events": events}

    async def _handle_find_free_slots(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle finding free slots."""
        # Parse date and duration from text
        # This is a simplified version - in reality, you'd use NLP to extract these
        input = FindFreeSlotsInput(
            provider=provider,
            user_id=user_id,
            range_start=datetime.now(),
            range_end=datetime.now(),
            duration_minutes=30
        )
        slots = await find_free_slots_tool(input)
        return {"slots": slots}

    async def _handle_create_event(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle creating an event."""
        # Parse event details from text
        # This is a simplified version - in reality, you'd use NLP to extract these
        input = CreateEventInput(
            provider=provider,
            user_id=user_id,
            summary="New Event",
            start=datetime.now(),
            end=datetime.now(),
            description="",
            location="",
            attendees=[]
        )
        event = await create_event_tool(input)
        return {"event": event}

    async def _handle_update_event(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle updating an event."""
        # Parse event details from text
        input = UpdateEventInput(
            provider=provider,
            user_id=user_id,
            event_id="event_id",  # This should be extracted from text
            summary="Updated Event",
            start=datetime.now(),
            end=datetime.now()
        )
        event = await update_event_tool(input)
        return {"event": event}

    async def _handle_delete_event(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle deleting an event."""
        input = DeleteEventInput(
            provider=provider,
            user_id=user_id,
            event_id="event_id"  # This should be extracted from text
        )
        success = await delete_event_tool(input)
        return {"success": success}

    async def _handle_reschedule_event(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle rescheduling an event."""
        input = RescheduleEventInput(
            provider=provider,
            user_id=user_id,
            event_id="event_id",  # This should be extracted from text
            new_start=datetime.now(),
            new_end=datetime.now()
        )
        event = await reschedule_event_tool(input)
        return {"event": event}

    async def _handle_cancel_event(self, text: str, user_id: str, provider: str) -> Dict[str, Any]:
        """Handle canceling an event."""
        input = CancelEventInput(
            provider=provider,
            user_id=user_id,
            event_id="event_id",  # This should be extracted from text
            start=datetime.now(),
            end=datetime.now()
        )
        success = await cancel_event_tool(input)
        return {"success": success}

async def run_calendar_agent(text: str, user_id: str, provider: str) -> Dict[str, Any]:
    """Run the calendar agent with the given input."""
    agent = CalendarAgent()
    return await agent.run(text, user_id, provider)

__all__ = ["run_calendar_agent"] 