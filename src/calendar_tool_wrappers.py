from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator
from src.tool_schemas import (
    ListEventsInput, ListEventsOutput,
    FreeSlotsInput, FreeSlotsOutput, FreeSlotSchema,
    CreateEventInput, CreateEventOutput,
    UpdateEventInput, UpdateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput,
    DeleteEventInput,
    EventSchema, AttendeeSchema
)
from pydantic import ValidationError
from src.services.oauth_service import OAuthService
from src.core.exceptions import ToolExecutionError
import pytest
import logging

logger = logging.getLogger(__name__)

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

async def update_event_tool(input: UpdateEventInput) -> UpdateEventOutput:
    """Update an existing calendar event."""
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Validate required fields
    if not input.event_id:
        raise ToolExecutionError("Event ID is required")
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # Get existing event
        existing_event = await calendar_service.get_event(
            event_id=input.event_id,
            calendar_id=input.calendar_id or "primary"
        )
        
        if not existing_event:
            raise ToolExecutionError(f"Event {input.event_id} not found")
        
        # Prepare update data
        update_data = {}
        if input.summary is not None:
            update_data["summary"] = input.summary
        if input.start is not None:
            update_data["start"] = {"dateTime": input.start.isoformat()}
        if input.end is not None:
            update_data["end"] = {"dateTime": input.end.isoformat()}
        if input.description is not None:
            update_data["description"] = input.description
        if input.location is not None:
            update_data["location"] = input.location
        if input.attendees is not None:
            update_data["attendees"] = input.attendees
        
        # Validate end time is after start time if both are being updated
        if "start" in update_data and "end" in update_data:
            start_time = datetime.fromisoformat(update_data["start"]["dateTime"])
            end_time = datetime.fromisoformat(update_data["end"]["dateTime"])
            if end_time <= start_time:
                raise ToolExecutionError("End time must be after start time")
        
        # Update event
        updated_event = await calendar_service.update_event(
            event_id=input.event_id,
            event_data=update_data,
            calendar_id=input.calendar_id or "primary"
        )
        
        # Map service event to tool event
        tool_event = _map_service_event_to_tool_event(updated_event)
        
        return UpdateEventOutput(event=tool_event)
        
    except Exception as e:
        error_msg = f"Failed to update event: {str(e)}"
        logger.error(error_msg)
        raise ToolExecutionError(error_msg, original_exception=e)

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

def _map_service_event_to_tool_event(event: dict) -> EventSchema:
    """Map service event to tool event schema."""
    return EventSchema(
        id=event.get('id', ''),
        summary=event.get('summary', ''),
        start=event.get('start', {}).get('dateTime', ''),
        end=event.get('end', {}).get('dateTime', ''),
        description=event.get('description', ''),
        location=event.get('location', {}).get('displayName', '') if isinstance(event.get('location'), dict) else event.get('location', ''),
        attendees=[
            AttendeeSchema(
                email=attendee.get('email', ''),
                name=attendee.get('displayName', '')
            )
            for attendee in event.get('attendees', [])
        ],
        html_link=event.get('htmlLink', '')
    )

class ListEventsInput(BaseModel):
    provider: str
    user_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_results: Optional[int] = 10

class ListEventsOutput(BaseModel):
    events: List[EventSchema] = Field(default_factory=list)

class FreeSlotsInput(BaseModel):
    provider: str
    user_id: str
    duration_minutes: int
    range_start: datetime
    range_end: datetime

    @field_validator('duration_minutes')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v

class FreeSlotsOutput(BaseModel):
    slots: List[FreeSlotSchema] = Field(default_factory=list)

class CreateEventInput(BaseModel):
    provider: str
    user_id: str
    summary: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[AttendeeSchema]] = Field(default_factory=list)

    @field_validator('end')
    def validate_dates(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError("End time must be after start time")
        return v

class CreateEventOutput(BaseModel):
    event: EventSchema

class UpdateEventInput(BaseModel):
    provider: str
    user_id: str
    event_id: str
    summary: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[AttendeeSchema]] = Field(default_factory=list)

    @field_validator('end')
    def validate_dates(cls, v, values):
        if v and 'start' in values and values['start'] and v <= values['start']:
            raise ValueError("End time must be after start time")
        return v

class UpdateEventOutput(BaseModel):
    event: EventSchema

class DeleteEventInput(BaseModel):
    provider: str
    user_id: str
    event_id: str

class DeleteEventOutput(BaseModel):
    success: bool

class RescheduleEventInput(BaseModel):
    provider: str
    user_id: str
    event_id: str
    new_start: datetime
    new_end: datetime

    @field_validator('new_end')
    def validate_dates(cls, v, values):
        if 'new_start' in values and v <= values['new_start']:
            raise ValueError("New end time must be after new start time")
        return v

class RescheduleEventOutput(BaseModel):
    event: EventSchema

class CancelEventInput(BaseModel):
    provider: str
    user_id: str
    event_id: str
    start: datetime
    end: datetime

    @field_validator('end')
    def validate_dates(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError("End time must be after start time")
        return v

class CancelEventOutput(BaseModel):
    success: bool

async def list_events_tool(input: ListEventsInput) -> ListEventsOutput:
    """List calendar events for a user within a specified time range."""
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Convert string dates to datetime if needed
    start = input.start_time or datetime.now()
    end = input.end_time or (start + timedelta(days=7))
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # List events
        events = await calendar_service.list_events(
            start_time=start,
            end_time=end,
            calendar_id=input.calendar_id or "primary",
            max_results=input.max_results or 10
        )
        
        # Map service events to tool events
        tool_events = []
        for event in events:
            try:
                tool_event = _map_service_event_to_tool_event(event)
                tool_events.append(tool_event)
            except Exception as e:
                logger.warning(f"Failed to map event: {e}")
                continue
        
        return ListEventsOutput(events=tool_events)
        
    except Exception as e:
        error_msg = f"Failed to list events: {str(e)}"
        logger.error(error_msg)
        raise ToolExecutionError(error_msg, original_exception=e)

async def find_free_slots_tool(input: FreeSlotsInput) -> FreeSlotsOutput:
    """Find free time slots for a user within a specified range."""
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    if input.duration_minutes <= 0:
        raise ToolExecutionError("Duration must be positive")
    if input.range_end <= input.range_start:
        raise ToolExecutionError("End of range must be after start of range")
    try:
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        slots = await calendar_service.find_free_slots(
            duration_minutes=input.duration_minutes,
            range_start=input.range_start,
            range_end=input.range_end
        )
        tool_slots = []
        for slot in slots:
            try:
                tool_slots.append(FreeSlotSchema(**slot))
            except Exception as e:
                logger.warning(f"Failed to map slot: {e}")
        return FreeSlotsOutput(slots=tool_slots)
    except Exception as e:
        error_msg = f"Failed to find free slots: {str(e)}"
        logger.error(error_msg)
        raise ToolExecutionError(error_msg, original_exception=e)

async def create_event_tool(input: CreateEventInput) -> CreateEventOutput:
    """Create a new calendar event."""
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Validate required fields
    if not input.summary:
        raise ToolExecutionError("Event summary is required")
    if not input.start:
        raise ToolExecutionError("Start time is required")
    if not input.end and not input.duration_minutes:
        raise ToolExecutionError("Either end time or duration is required")
    
    try:
        # Calculate end time if duration is provided
        end_time = input.end
        if not end_time and input.duration_minutes:
            end_time = input.start + timedelta(minutes=input.duration_minutes)
        
        # Validate end time is after start time
        if end_time <= input.start:
            raise ToolExecutionError("End time must be after start time")
        
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # Create event
        event_data = {
            "summary": input.summary,
            "start": {"dateTime": input.start.isoformat()},
            "end": {"dateTime": end_time.isoformat()},
            "description": input.description,
            "location": input.location,
            "attendees": input.attendees or []
        }
        
        created_event = await calendar_service.create_event(
            event_data=event_data,
            calendar_id=input.calendar_id or "primary"
        )
        
        # Map service event to tool event
        tool_event = _map_service_event_to_tool_event(created_event)
        
        return CreateEventOutput(event=tool_event)
        
    except Exception as e:
        error_msg = f"Failed to create event: {str(e)}"
        logger.error(error_msg)
        raise ToolExecutionError(error_msg, original_exception=e)

async def delete_event_tool(input: DeleteEventInput) -> DeleteEventOutput:
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    return DeleteEventOutput(success=True)

async def reschedule_event_tool(input: RescheduleEventInput) -> RescheduleEventOutput:
    """Reschedule an existing calendar event."""
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    if not input.event_id:
        raise ToolExecutionError("Event ID is required")
    if input.new_end <= input.new_start:
        raise ToolExecutionError("New end time must be after new start time")
    try:
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        updated_event = await calendar_service.reschedule_event(
            event_id=input.event_id,
            new_start=input.new_start,
            new_end=input.new_end,
            calendar_id=getattr(input, 'calendar_id', 'primary')
        )
        tool_event = _map_service_event_to_tool_event(updated_event)
        return RescheduleEventOutput(event=tool_event)
    except Exception as e:
        error_msg = f"Failed to reschedule event: {str(e)}"
        logger.error(error_msg)
        raise ToolExecutionError(error_msg, original_exception=e)

async def cancel_event_tool(input: CancelEventInput) -> CancelEventOutput:
    """Cancel a calendar event."""
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    if not input.event_id:
        raise ToolExecutionError("Event ID is required")
    if input.end <= input.start:
        raise ToolExecutionError("End time must be after start time")
    try:
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        success = await calendar_service.cancel_event(
            event_id=input.event_id,
            start=input.start,
            end=input.end,
            calendar_id=getattr(input, 'calendar_id', 'primary')
        )
        return CancelEventOutput(success=success)
    except Exception as e:
        error_msg = f"Failed to cancel event: {str(e)}"
        logger.error(error_msg)
        raise ToolExecutionError(error_msg, original_exception=e)

class TestListEventsTool:
    def test_google_success(self):
        now = datetime.utcnow().isoformat()
        input = ListEventsInput(provider="google", user_id="u1", start_time=now, end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat())
        output = list_events_tool(input)
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 1
        assert all(isinstance(ev, EventSchema) for ev in output.events)

    def test_microsoft_success(self):
        now = datetime.utcnow().isoformat()
        input = ListEventsInput(provider="microsoft", user_id="u1", start_time=now, end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat())
        output = list_events_tool(input)
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 1
        assert all(isinstance(ev, EventSchema) for ev in output.events)

    def test_unknown_provider(self):
        now = datetime.utcnow().isoformat()
        input = ListEventsInput(provider="other", user_id="u1", start_time=now, end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat())
        with pytest.raises(ToolExecutionError):
            list_events_tool(input) 