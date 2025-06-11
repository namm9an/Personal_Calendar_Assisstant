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
from src.services.google_calendar_service import GoogleCalendarService
from src.services.microsoft_calendar_service import MicrosoftCalendarService
import pytest
import logging

logger = logging.getLogger(__name__)

async def get_calendar_service(provider: str, user_id: str):
    """Get calendar service for the provider and user."""
    oauth_service = OAuthService()
    user = await oauth_service.get_user_by_id(user_id)
    
    if not user:
        raise ToolExecutionError(f"User not found: {user_id}")
    
    if provider == "google":
        if not user.google_access_token:
            raise ToolExecutionError("No Google credentials available for this user")
        return GoogleCalendarService(access_token=user.google_access_token)
    elif provider == "microsoft":
        if not user.microsoft_access_token:
            raise ToolExecutionError("No Microsoft credentials available for this user")
        return MicrosoftCalendarService(access_token=user.microsoft_access_token)
    else:
        raise ToolExecutionError(f"Unsupported provider: {provider}")

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
    """Tool for updating calendar events."""
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
        raise ToolExecutionError(error_msg)

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
    # Extract start time
    start_time = ""
    start_dict = event.get('start', {})
    if isinstance(start_dict, dict):
        if 'dateTime' in start_dict:
            if isinstance(start_dict['dateTime'], dict):
                # Handle nested dateTime objects
                start_time = start_dict['dateTime'].get('dateTime', '')
            elif isinstance(start_dict['dateTime'], datetime):
                # Handle datetime objects directly
                start_time = start_dict['dateTime'].isoformat()
            else:
                # Handle normal dateTime strings
                start_time = start_dict['dateTime']
        elif 'date' in start_dict:
            # Handle all-day events
            start_time = start_dict['date']
    elif isinstance(start_dict, str):
        # Handle direct string values
        start_time = start_dict
    elif isinstance(start_dict, datetime):
        # Handle direct datetime values
        start_time = start_dict.isoformat()
    
    # Extract end time
    end_time = ""
    end_dict = event.get('end', {})
    if isinstance(end_dict, dict):
        if 'dateTime' in end_dict:
            if isinstance(end_dict['dateTime'], dict):
                # Handle nested dateTime objects
                end_time = end_dict['dateTime'].get('dateTime', '')
            elif isinstance(end_dict['dateTime'], datetime):
                # Handle datetime objects directly
                end_time = end_dict['dateTime'].isoformat()
            else:
                # Handle normal dateTime strings
                end_time = end_dict['dateTime']
        elif 'date' in end_dict:
            # Handle all-day events
            end_time = end_dict['date']
    elif isinstance(end_dict, str):
        # Handle direct string values
        end_time = end_dict
    elif isinstance(end_dict, datetime):
        # Handle direct datetime values
        end_time = end_dict.isoformat()
    
    # Get the summary/subject (different naming conventions between providers)
    summary = event.get('summary', event.get('subject', ''))
    
    # Get location - can be a string or an object with displayName
    location = ""
    loc_data = event.get('location', '')
    if isinstance(loc_data, dict):
        location = loc_data.get('displayName', '')
    else:
        location = str(loc_data)
    
    # Get attendees - can be a list of objects with email and name
    attendees = []
    for attendee in event.get('attendees', []):
        email = attendee.get('email', '')
        name = attendee.get('name', '')
        response_status = attendee.get('responseStatus', None)
        if email:
            attendees.append(AttendeeSchema(email=email, name=name, response_status=response_status))
    
    # Get HTML link
    html_link = event.get('htmlLink', event.get('webLink', ''))
    
    # Get description
    description = event.get('description', '')
    
    # Get ID - can be direct ID or Microsoft's ID format
    event_id = event.get('id', '')
    if not event_id and 'iCalUId' in event:
        event_id = event['iCalUId']
    
    return EventSchema(
        id=event_id,
        summary=summary,
        start=start_time,
        end=end_time,
        description=description,
        location=location,
        attendees=attendees,
        html_link=html_link
    )

class ListEventsInput(BaseModel):
    provider: str
    user_id: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    max_results: Optional[int] = 10
    calendar_id: Optional[str] = None

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
    def validate_dates(cls, v, info):
        data = info.data
        if 'start' in data and v <= data['start']:
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
    def validate_dates(cls, v, info):
        data = info.data
        if v and 'start' in data and data['start'] and v <= data['start']:
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
    def validate_dates(cls, v, info):
        data = info.data
        if 'new_start' in data and v <= data['new_start']:
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
    def validate_dates(cls, v, info):
        data = info.data
        if 'start' in data and v <= data['start']:
            raise ValueError("End time must be after start time")
        return v

class CancelEventOutput(BaseModel):
    success: bool

async def list_events_tool(input: ListEventsInput) -> ListEventsOutput:
    """List calendar events."""
    if input.provider not in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # List events
        events = await calendar_service.list_events(
            time_min=input.start,
            time_max=input.end,
            calendar_id=input.calendar_id or "primary",
            max_results=input.max_results
        )
        
        # Map service events to tool events
        tool_events = []
        for event in events:
            try:
                tool_event = _map_service_event_to_tool_event(event)
                tool_events.append(tool_event)
            except Exception as e:
                # Log error but continue processing other events
                logger.error(f"Error mapping event: {e}")
        
        return ListEventsOutput(events=tool_events)
        
    except ToolExecutionError as e:
        # Re-raise ToolExecutionError directly
        raise e
    except Exception as e:
        # Handle different error types
        error_msg = str(e)
        if "User not found" in error_msg:
            raise ToolExecutionError(f"User not found: {input.user_id}")
        elif "No credentials" in error_msg or "credentials" in error_msg.lower():
            raise ToolExecutionError(f"No {input.provider} credentials available for this user")
        elif isinstance(e, TimeoutError):
            error_msg = "Connection timed out when listing events. Please try again."
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        else:
            error_msg = f"Failed to list events: {error_msg}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

async def find_free_slots_tool(input: FreeSlotsInput) -> FreeSlotsOutput:
    """Find free time slots."""
    if input.provider not in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Validate duration
    if input.duration_minutes <= 0:
        raise ToolExecutionError("Duration must be positive")
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # Find free slots
        slots = await calendar_service.find_free_slots(
            duration_minutes=input.duration_minutes,
            range_start=input.range_start,
            range_end=input.range_end
        )
        
        # Map service slots to tool slots
        tool_slots = []
        for slot in slots:
            # Handle different formats for time slots
            start_time = ""
            end_time = ""
            
            if isinstance(slot, dict):
                # Handle dictionary format
                start_time = slot.get('start', '')
                end_time = slot.get('end', '')
                
                # Handle nested dateTime objects
                if isinstance(start_time, dict) and 'dateTime' in start_time:
                    start_time = start_time['dateTime']
                if isinstance(end_time, dict) and 'dateTime' in end_time:
                    end_time = end_time['dateTime']
            
            tool_slots.append(FreeSlotSchema(start=start_time, end=end_time))
        
        return FreeSlotsOutput(slots=tool_slots)
        
    except ToolExecutionError as e:
        # Re-raise ToolExecutionError directly
        raise e
    except Exception as e:
        # Handle different error types
        error_msg = str(e)
        if "User not found" in error_msg:
            raise ToolExecutionError(f"User not found: {input.user_id}")
        elif "No credentials" in error_msg or "credentials" in error_msg.lower():
            raise ToolExecutionError(f"No {input.provider} credentials available for this user")
        elif isinstance(e, TimeoutError):
            error_msg = f"Failed to find free slots: Connection timeout"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        else:
            error_msg = f"Failed to find free slots: {error_msg}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

async def create_event_tool(input: CreateEventInput) -> CreateEventOutput:
    """Create a new calendar event."""
    if input.provider not in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Validate required fields
    if not input.summary:
        raise ToolExecutionError("Event summary is required")
    if not input.start:
        raise ToolExecutionError("Event start time is required")
    if not input.end:
        raise ToolExecutionError("Event end time is required")
    if input.end <= input.start:
        raise ToolExecutionError("End time must be after start time")
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # Prepare event data
        event_data = {
            "summary": input.summary,
            "start": input.start,
            "end": input.end
        }
        
        if input.description:
            event_data["description"] = input.description
        if input.location:
            event_data["location"] = input.location
        if input.attendees:
            event_data["attendees"] = [
                {"email": attendee.email, "name": attendee.name}
                for attendee in input.attendees
            ]
        
        # Create event
        # Set default calendar_id to "primary" if not present in the input
        calendar_id = "primary"
        if hasattr(input, 'calendar_id') and input.calendar_id:
            calendar_id = input.calendar_id
            
        created_event = await calendar_service.create_event(
            event_data=event_data,
            calendar_id=calendar_id
        )
        
        # Map service event to tool event
        tool_event = _map_service_event_to_tool_event(created_event)
        
        return CreateEventOutput(event=tool_event)
        
    except ToolExecutionError as e:
        # Re-raise ToolExecutionError directly
        raise e
    except Exception as e:
        # Handle different error types
        error_msg = str(e)
        if "User not found" in error_msg:
            raise ToolExecutionError(f"User not found: {input.user_id}")
        elif "No credentials" in error_msg or "credentials" in error_msg.lower():
            raise ToolExecutionError(f"No {input.provider} credentials available for this user")
        elif "conflict" in error_msg.lower() or "409" in error_msg:
            raise ToolExecutionError(f"Event conflicts with an existing event")
        elif isinstance(e, TimeoutError):
            error_msg = "Connection timed out when creating event. Please try again."
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        else:
            error_msg = f"Failed to create event: {error_msg}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

async def delete_event_tool(input: DeleteEventInput) -> DeleteEventOutput:
    if not input.provider in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    return DeleteEventOutput(success=True)

async def reschedule_event_tool(input: RescheduleEventInput) -> RescheduleEventOutput:
    """Reschedule an existing calendar event."""
    if input.provider not in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Validate required fields
    if not input.event_id:
        raise ToolExecutionError("Event ID is required")
    if not input.new_start:
        raise ToolExecutionError("New start time is required")
    if not input.new_end:
        raise ToolExecutionError("New end time is required")
    if input.new_end <= input.new_start:
        raise ToolExecutionError("End time must be after start time")
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # Prepare update data with new times
        update_data = {
            "start": input.new_start,
            "end": input.new_end,
            "summary": "Rescheduled Event",  # Add summary for Google
            "subject": "Rescheduled Event"   # Add subject for Microsoft
        }
        
        # Set default calendar_id
        calendar_id = "primary"
        # Try to get calendar_id from input if it exists
        try:
            if hasattr(input, 'calendar_id') and input.calendar_id:
                calendar_id = input.calendar_id
        except (AttributeError, Exception):
            # If calendar_id is not available, use default
            pass
        
        # Update event with new times
        updated_event = await calendar_service.update_event(
            event_id=input.event_id,
            event_data=update_data,
            calendar_id=calendar_id
        )
        
        # Map service event to tool event
        tool_event = _map_service_event_to_tool_event(updated_event)
        
        return RescheduleEventOutput(event=tool_event)
        
    except ToolExecutionError as e:
        # Re-raise ToolExecutionError directly
        raise e
    except Exception as e:
        # Handle different error types
        error_msg = str(e)
        if "User not found" in error_msg:
            raise ToolExecutionError(f"User not found: {input.user_id}")
        elif "No credentials" in error_msg or "credentials" in error_msg.lower():
            raise ToolExecutionError(f"No {input.provider} credentials available for this user")
        elif "not found" in error_msg.lower() or "404" in error_msg:
            raise ToolExecutionError(f"Event {input.event_id} not found")
        elif "conflict" in error_msg.lower() or "409" in error_msg:
            raise ToolExecutionError(f"Event conflicts with an existing event")
        elif isinstance(e, TimeoutError):
            error_msg = "Connection timed out when rescheduling event. Please try again."
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        else:
            error_msg = f"Failed to reschedule event: {error_msg}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

async def cancel_event_tool(input: CancelEventInput) -> CancelEventOutput:
    """Cancel an existing calendar event."""
    if input.provider not in ("google", "microsoft"):
        raise ToolExecutionError(f"Unsupported provider: {input.provider}")
    
    # Validate required fields
    if not input.event_id:
        raise ToolExecutionError("Event ID is required")
    
    try:
        # Get calendar service for the provider
        calendar_service = await get_calendar_service(input.provider, input.user_id)
        
        # Set default calendar_id
        calendar_id = "primary"
        # Try to get calendar_id from input if it exists
        try:
            if hasattr(input, 'calendar_id') and input.calendar_id:
                calendar_id = input.calendar_id
        except (AttributeError, Exception):
            # If calendar_id is not available, use default
            pass
        
        # Cancel event
        await calendar_service.cancel_event(
            event_id=input.event_id,
            start=input.start,
            end=input.end,
            calendar_id=calendar_id
        )
        
        return CancelEventOutput(success=True)
        
    except ToolExecutionError as e:
        # Re-raise ToolExecutionError directly
        raise e
    except Exception as e:
        # Handle different error types
        error_msg = str(e)
        if "User not found" in error_msg:
            raise ToolExecutionError(f"User not found: {input.user_id}")
        elif "No credentials" in error_msg or "credentials" in error_msg.lower():
            raise ToolExecutionError(f"No {input.provider} credentials available for this user")
        elif "not found" in error_msg.lower() or "404" in error_msg:
            raise ToolExecutionError(f"Event {input.event_id} not found")
        elif isinstance(e, TimeoutError):
            error_msg = "Connection timed out when canceling event. Please try again."
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        else:
            error_msg = f"Failed to cancel event: {error_msg}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

class TestListEventsTool:
    def test_google_success(self):
        now = datetime.utcnow().isoformat()
        input = ListEventsInput(provider="google", user_id="u1", start=now, end=(datetime.utcnow() + timedelta(hours=1)).isoformat())
        output = list_events_tool(input)
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 1
        assert all(isinstance(ev, EventSchema) for ev in output.events)

    def test_microsoft_success(self):
        now = datetime.utcnow().isoformat()
        input = ListEventsInput(provider="microsoft", user_id="u1", start=now, end=(datetime.utcnow() + timedelta(hours=1)).isoformat())
        output = list_events_tool(input)
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 1
        assert all(isinstance(ev, EventSchema) for ev in output.events)

    def test_unknown_provider(self):
        now = datetime.utcnow().isoformat()
        input = ListEventsInput(provider="other", user_id="u1", start=now, end=(datetime.utcnow() + timedelta(hours=1)).isoformat())
        with pytest.raises(ToolExecutionError):
            list_events_tool(input) 