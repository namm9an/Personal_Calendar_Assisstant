from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.tool_schemas import (
    ListEventsInput, ListEventsOutput,
    FreeSlotsInput, FreeSlotsOutput, FreeSlotSchema,
    CreateEventInput, CreateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput,
    EventSchema
)
from pydantic import ValidationError
from src.services.oauth_service import OAuthService

class ToolExecutionError(Exception):
    """Custom exception for tool execution errors."""
    pass

class BaseCalendarWrapper:
    """Base class for calendar tool wrappers."""
    def __init__(self, calendar_service):
        self.calendar_service = calendar_service

    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> None:
        """Validate that all required fields are present in the data."""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ToolExecutionError(f"Missing required fields: {', '.join(missing_fields)}")

class CreateEventWrapper(BaseCalendarWrapper):
    """Wrapper for creating calendar events."""
    def execute(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate required fields
            self.validate_required_fields(event_data, ['summary', 'start', 'end'])
            
            # Create the event
            event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            return event
        except Exception as e:
            raise ToolExecutionError(f"Failed to create event: {str(e)}")

class ListEventsWrapper(BaseCalendarWrapper):
    """Wrapper for listing calendar events."""
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate required fields
            self.validate_required_fields(params, ['timeMin'])
            
            # List events
            events = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=params['timeMin'],
                maxResults=params.get('maxResults', 10),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events
        except Exception as e:
            raise ToolExecutionError(f"Failed to list events: {str(e)}")

class UpdateEventWrapper(BaseCalendarWrapper):
    """Wrapper for updating calendar events."""
    def execute(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate required fields
            self.validate_required_fields(event_data, ['eventId'])
            
            # Update the event
            event = self.calendar_service.events().update(
                calendarId='primary',
                eventId=event_data['eventId'],
                body=event_data
            ).execute()
            
            return event
        except Exception as e:
            raise ToolExecutionError(f"Failed to update event: {str(e)}")

class DeleteEventWrapper(BaseCalendarWrapper):
    """Wrapper for deleting calendar events."""
    def execute(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate required fields
            self.validate_required_fields(event_data, ['eventId'])
            
            # Delete the event
            self.calendar_service.events().delete(
                calendarId='primary',
                eventId=event_data['eventId']
            ).execute()
            
            return {'status': 'success'}
        except Exception as e:
            raise ToolExecutionError(f"Failed to delete event: {str(e)}")

def list_events_tool(input: ListEventsInput) -> ListEventsOutput:
    oauth_service = OAuthService()
    access_token, refresh_token = oauth_service.get_user_tokens(input.user_id, input.provider)
    if not access_token:
        raise ToolExecutionError("No credentials found for user or token expired.")
    # Provider logic stub
    if input.provider == "google":
        # Return two dummy events
        events = [
            EventSchema(id="1", summary="Google Event 1", start=input.start, end=input.end),
            EventSchema(id="2", summary="Google Event 2", start=input.start, end=input.end)
        ]
        return ListEventsOutput(events=events)
    elif input.provider == "microsoft":
        events = [
            EventSchema(id="3", summary="MS Event 1", start=input.start, end=input.end)
        ]
        return ListEventsOutput(events=events)
    else:
        raise ToolExecutionError("Unknown provider")

def find_free_slots_tool(input: FreeSlotsInput) -> FreeSlotsOutput:
    # Provider logic stub
    if input.provider in ("google", "microsoft"):
        slots = [
            FreeSlotSchema(start=input.range_start, end=input.range_start + timedelta(minutes=input.duration_minutes)),
            FreeSlotSchema(start=input.range_start + timedelta(hours=1), end=input.range_start + timedelta(hours=1, minutes=input.duration_minutes))
        ]
        return FreeSlotsOutput(slots=slots)
    else:
        raise ToolExecutionError("Unknown provider")

def create_event_tool(input: CreateEventInput) -> CreateEventOutput:
    # Provider logic stub
    if not input.summary:
        raise ToolExecutionError("Missing summary")
    event = EventSchema(
        id="new-event",
        summary=input.summary,
        start=input.start,
        end=input.end,
        description=input.description,
        location=input.location,
        attendees=input.attendees
    )
    return CreateEventOutput(event=event)

def reschedule_event_tool(input: RescheduleEventInput) -> RescheduleEventOutput:
    # Provider logic stub
    if input.provider in ("google", "microsoft"):
        event = EventSchema(
            id=input.event_id,
            summary="Rescheduled Event",
            start=input.new_start,
            end=input.new_start + timedelta(hours=1)
        )
        return RescheduleEventOutput(event=event)
    else:
        raise ToolExecutionError("Unknown provider")

def cancel_event_tool(input: CancelEventInput) -> CancelEventOutput:
    # Provider logic stub
    if input.provider in ("google", "microsoft"):
        return CancelEventOutput(success=True)
    else:
        raise ToolExecutionError("Unknown provider") 