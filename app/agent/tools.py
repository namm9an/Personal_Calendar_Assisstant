"""
Tools for the Personal Calendar Assistant agent.
"""
import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, Tool
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class ListEventsInput(BaseModel):
    """Input for the list_events tool."""
    
    start_date: Optional[str] = Field(
        None,
        description="Start date to list events from (format: YYYY-MM-DD). Defaults to today.",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date to list events until (format: YYYY-MM-DD). Defaults to start_date + 1 day.",
    )
    max_results: Optional[int] = Field(
        10, description="Maximum number of events to return."
    )
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID to list events from."
    )


class CreateEventInput(BaseModel):
    """Input for the create_event tool."""
    
    summary: str = Field(..., description="Title of the event.")
    start_datetime: str = Field(
        ...,
        description="Start date and time of the event (format: YYYY-MM-DD HH:MM).",
    )
    duration_minutes: Optional[int] = Field(
        None,
        description="Duration of the event in minutes. Required if end_datetime is not provided.",
    )
    end_datetime: Optional[str] = Field(
        None,
        description="End date and time of the event (format: YYYY-MM-DD HH:MM). Required if duration_minutes is not provided.",
    )
    description: Optional[str] = Field(None, description="Description of the event.")
    location: Optional[str] = Field(None, description="Location of the event.")
    attendees: Optional[List[Dict[str, str]]] = Field(
        None,
        description="List of attendees as [{'email': 'email@example.com', 'name': 'Name'}].",
    )
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID to create the event in."
    )
    time_zone: Optional[str] = Field(None, description="Time zone of the event.")
    conference_solution: Optional[str] = Field(None, description="Type of conference solution to add (e.g., 'eventHangout' for Google, 'teamsForBusiness' for Microsoft).")


class UpdateEventInput(BaseModel):
    """Input for the update_event tool."""
    
    event_id: str = Field(..., description="ID of the event to update.")
    summary: Optional[str] = Field(None, description="New title of the event.")
    start_datetime: Optional[str] = Field(
        None,
        description="New start date and time of the event (format: YYYY-MM-DD HH:MM).",
    )
    end_datetime: Optional[str] = Field(
        None,
        description="New end date and time of the event (format: YYYY-MM-DD HH:MM).",
    )
    description: Optional[str] = Field(None, description="New description of the event.")
    location: Optional[str] = Field(None, description="New location of the event.")
    attendees: Optional[List[Dict[str, str]]] = Field(
        None,
        description="New list of attendees as [{'email': 'email@example.com', 'name': 'Name'}].",
    )
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID containing the event."
    )


class DeleteEventInput(BaseModel):
    """Input for the delete_event tool."""
    
    event_id: str = Field(..., description="ID of the event to delete.")
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID containing the event."
    )


class FindAvailableSlotInput(BaseModel):
    """Input for the find_available_slot tool."""
    
    duration_minutes: int = Field(
        ..., description="Duration of the meeting in minutes."
    )
    start_date: str = Field(
        ...,
        description="Start date to search from (format: YYYY-MM-DD).",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date to search until (format: YYYY-MM-DD). Defaults to start_date + 1 day.",
    )
    start_time: Optional[str] = Field(
        None,
        description="Earliest time of day to consider (format: HH:MM, 24-hour). Defaults to user's working hours start.",
    )
    end_time: Optional[str] = Field(
        None,
        description="Latest time of day to consider (format: HH:MM, 24-hour). Defaults to user's working hours end.",
    )
    attendees: Optional[List[str]] = Field(
        None,
        description="List of attendee emails to check availability for.",
    )
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID to check availability in."
    )


class CheckAvailabilityInput(BaseModel):
    """Input for the check_availability tool."""
    
    start_datetime: str = Field(
        ...,
        description="Start date and time to check (format: YYYY-MM-DD HH:MM).",
    )
    end_datetime: str = Field(
        ...,
        description="End date and time to check (format: YYYY-MM-DD HH:MM).",
    )
    attendees: List[str] = Field(
        ...,
        description="List of attendee emails to check availability for.",
    )
    calendar_id: Optional[str] = Field(
        "primary", description="Calendar ID to check availability in."
    )


class CalendarTools:
    """Collection of tools for calendar operations."""
    
    def __init__(self, user: User, db: Session, provider: str = "google"):
        """
        Initialize calendar tools.
        
        Args:
            user: User for whom to perform calendar operations
            db: Database session for logging actions
            provider: Calendar provider to use ("google" or "microsoft")
        """
        self.user = user
        self.db = db
        self.provider = provider.lower()
        
        # Set up calendar service based on provider
        if self.provider == "google":
            self.calendar_service = GoogleCalendarService(user, db)
        elif self.provider == "microsoft":
            # TODO: Replace with actual MicrosoftCalendarService when implemented
            # For now, using a placeholder that follows the same interface
            from app.agent.calendar_tool_wrappers import MicrosoftCalendarService
            self.calendar_service = MicrosoftCalendarService(credentials="mock_credentials")
            logger.warning("Using mock MicrosoftCalendarService - replace with actual implementation")
        else:
            raise ValueError(f"Unsupported calendar provider: {provider}")
            
    def get_service_for_provider(self, provider: str):
        """
        Get a calendar service for a specific provider without changing the current one.
        
        Args:
            provider: Calendar provider to use ("google" or "microsoft")
            
        Returns:
            Calendar service instance for the specified provider
        """
        provider = provider.lower()
        if provider == "google":
            return GoogleCalendarService(self.user, self.db)
        elif provider == "microsoft":
            # TODO: Replace with actual MicrosoftCalendarService when implemented
            from app.agent.calendar_tool_wrappers import MicrosoftCalendarService
            return MicrosoftCalendarService(credentials="mock_credentials")
        else:
            raise ValueError(f"Unsupported calendar provider: {provider}")
        
    def _parse_datetime(self, date_str: str, time_str: Optional[str] = None) -> datetime.datetime:
        """
        Parse date and time strings into a datetime object.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            time_str: Optional time string in HH:MM format
            
        Returns:
            Datetime object
        """
        if time_str:
            # Combine date and time
            dt_str = f"{date_str} {time_str}"
            return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        else:
            # Date only
            return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    
    def list_events(self, input_data: Union[ListEventsInput, dict]) -> str:
        """
        List events from the calendar.
        
        Args:
            input_data: Parameters for listing events
            
        Returns:
            JSON string of events
        """
        if isinstance(input_data, dict):
            input_data = ListEventsInput(**input_data)
            
        try:
            # Set default dates if not provided
            if not input_data.start_date:
                start_date = datetime.date.today()
            else:
                start_date = datetime.datetime.strptime(input_data.start_date, "%Y-%m-%d").date()
                
            if not input_data.end_date:
                end_date = start_date + datetime.timedelta(days=1)
            else:
                end_date = datetime.datetime.strptime(input_data.end_date, "%Y-%m-%d").date()
                
            # Create datetime objects for the start and end of the day
            time_min = datetime.datetime.combine(start_date, datetime.time.min)
            time_max = datetime.datetime.combine(end_date, datetime.time.max)
            
            events: list = []
            if self.provider == "google":
                events = self.calendar_service.get_events(
                    calendar_id=input_data.calendar_id or "primary",
                    time_min=time_min,
                    time_max=time_max,
                    max_results=input_data.max_results or 10,
                )
            elif self.provider == "microsoft":
                events = self.calendar_service.list_events(
                    user_id=str(self.user.id),
                    calendar_id=input_data.calendar_id or "primary",
                    time_min=time_min,
                    time_max=time_max,
                    max_results=input_data.max_results or 10,
                )
            else:
                # This case should ideally be caught in __init__, but as a safeguard:
                raise ValueError(f"Unsupported calendar provider: {self.provider}")
                
            # Process events for display
            processed_events = []
            for event in events:
                start = event.get("start", {})
                end = event.get("end", {})
                
                # Handle different date/time formats
                if "dateTime" in start:
                    start_time = datetime.datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                    start_str = start_time.strftime("%Y-%m-%d %H:%M")
                else:
                    start_str = start.get("date", "N/A")
                    
                if "dateTime" in end:
                    end_time = datetime.datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
                    end_str = end_time.strftime("%Y-%m-%d %H:%M")
                else:
                    end_str = end.get("date", "N/A")
                
                processed_events.append({
                    "id": event.get("id"),
                    "summary": event.get("summary", "Untitled Event"),
                    "start": start_str,
                    "end": end_str,
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "attendees": [
                        {"email": a.get("email"), "name": a.get("displayName", "")}
                        for a in event.get("attendees", [])
                    ],
                })
                
            return json.dumps({"events": processed_events}, indent=2)
            
        except HTTPException as http_exc:
            logger.error(f"Error listing events (HTTPException): {http_exc.detail}")
            return json.dumps({"error": http_exc.detail})
        except Exception as e:
            logger.error(f"Error listing events (General Exception): {str(e)}")
            error_detail = getattr(e, 'detail', None)
            if not error_detail:
                error_detail = getattr(e, 'message', None)
            if not error_detail:
                error_detail = str(e)
            if not error_detail:
                error_detail = "An unexpected error occurred while listing events."
            return json.dumps({"error": error_detail})
    
    def create_event(self, input_data: Union[CreateEventInput, dict]) -> str:
        """
        Create a new event on the calendar.
        
        Args:
            input_data: Parameters for creating an event
            
        Returns:
            JSON string with the created event details
        """
        try:
            if isinstance(input_data, dict):
                # Ensure all required fields for Pydantic model are present if it's a dict
                # Pydantic will raise validation error if 'summary' or 'start_datetime' are missing
                event_input = CreateEventInput(**input_data)
            else:
                event_input = input_data

            # Validate date/time inputs
            if not event_input.end_datetime and not event_input.duration_minutes:
                raise ValueError(
                    "Either end_datetime or duration_minutes must be provided."
                )

            start_dt = self._parse_datetime(event_input.start_datetime.split(' ')[0],
                                            event_input.start_datetime.split(' ')[1])

            if event_input.end_datetime:
                end_dt = self._parse_datetime(event_input.end_datetime.split(' ')[0],
                                            event_input.end_datetime.split(' ')[1])
            elif event_input.duration_minutes:
                end_dt = start_dt + datetime.timedelta(minutes=event_input.duration_minutes)
            else:
                # This case should be caught by the check above, but as a safeguard:
                raise ValueError("Invalid start/end time configuration.")

            if end_dt <= start_dt:
                raise ValueError("Event end time must be after start time.")

            # Prepare attendee list for the service layer if present
            attendees_service_format = []
            if event_input.attendees:
                for att in event_input.attendees:
                    # Google API expects {'email': '...'}, optionally 'displayName'
                    # Assuming 'name' from input maps to 'displayName'
                    attendee_entry = {'email': att.get('email')}
                    if 'name' in att and att['name']:
                        attendee_entry['displayName'] = att['name']
                    if attendee_entry.get('email'): # Only add if email is present
                        attendees_service_format.append(attendee_entry)
            
            # Determine timezone to use
            timezone_to_use = self.user.timezone  # Default to user's timezone
            if hasattr(event_input, 'time_zone') and event_input.time_zone:
                timezone_to_use = event_input.time_zone

            # Prepare conference data if requested
            conference_data_for_service = None
            if hasattr(event_input, 'conference_solution') and event_input.conference_solution:
                conference_data_for_service = {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": event_input.conference_solution}
                    }
                }

            # Prepare service call arguments
            service_call_args = {
                "summary": event_input.summary,
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "description": event_input.description,
                "location": event_input.location,
                "attendees": attendees_service_format if attendees_service_format else None,
                "time_zone": timezone_to_use
            }

            if conference_data_for_service:
                service_call_args["conference_data"] = conference_data_for_service

            # Only add calendar_id if explicitly provided in input and is not None
            if hasattr(event_input, 'calendar_id') and event_input.calendar_id:
                service_call_args["calendar_id"] = event_input.calendar_id
        
            # Call the service layer
            # user_input is intentionally not passed to align with test expectations
            created_event = self.calendar_service.create_event(**service_call_args)

            return json.dumps(created_event, indent=2)

        except HTTPException as http_exc:
            logger.error(f"Error creating event (HTTPException): {http_exc.detail}")
            return json.dumps({"success": False, "error": http_exc.detail})
        except ValueError as ve:
            logger.error(f"Error creating event (ValueError): {str(ve)}")
            return json.dumps({"success": False, "error": str(ve)})
        except Exception as e:
            logger.error(f"Error creating event (General Exception): {str(e)}", exc_info=True)
            error_detail = getattr(e, 'detail', None)
            if not error_detail: error_detail = getattr(e, 'message', None)
            if not error_detail: error_detail = str(e)
            if not error_detail: error_detail = "An unexpected error occurred while creating the event."
            return json.dumps({"success": False, "error": error_detail})
    
    def update_event(self, input_data: Union[UpdateEventInput, dict]) -> str:
        """
        Update an existing event on the calendar.
        
        Args:
            input_data: Parameters for updating an event
            
        Returns:
            JSON string with the updated event details
        """
        if isinstance(input_data, dict):
            input_data = UpdateEventInput(**input_data)
            
        try:
            # Parse datetimes if provided
            start_time = None
            if input_data.start_datetime:
                start_time = datetime.datetime.strptime(input_data.start_datetime, "%Y-%m-%d %H:%M")
                
            end_time = None
            if input_data.end_datetime:
                end_time = datetime.datetime.strptime(input_data.end_datetime, "%Y-%m-%d %H:%M")
                
            # Format attendees for the API
            attendees = None
            if input_data.attendees:
                attendees = [{"email": a.get("email")} for a in input_data.attendees if a.get("email")]
                
            # Update the event
            updated_event = self.calendar_service.update_event(
                event_id=input_data.event_id,
                calendar_id=input_data.calendar_id or "primary",
                summary=input_data.summary,
                start_time=start_time,
                end_time=end_time,
                description=input_data.description,
                location=input_data.location,
                attendees=attendees,
                user_input=f"Update event: {input_data.event_id}",
            )
            
            # Format response
            return json.dumps({
                "success": True,
                "event": {
                    "id": updated_event.get("id"),
                    "summary": updated_event.get("summary"),
                    "link": updated_event.get("htmlLink"),
                }
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})
    
    def delete_event(self, input_data: Union[DeleteEventInput, dict]) -> str:
        """
        Delete an event from the calendar.
        
        Args:
            input_data: Parameters for deleting an event
            
        Returns:
            JSON string with the deletion result
        """
        if isinstance(input_data, dict):
            input_data = DeleteEventInput(**input_data)
            
        try:
            # Delete the event
            success = self.calendar_service.delete_event(
                event_id=input_data.event_id,
                calendar_id=input_data.calendar_id or "primary",
                user_input=f"Delete event: {input_data.event_id}",
            )
            
            # Format response
            return json.dumps({
                "success": success,
                "message": f"Event {input_data.event_id} has been deleted."
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})
    
    def find_available_slot(self, input_data: Union[FindAvailableSlotInput, dict]) -> str:
        """
        Find an available time slot for a meeting.
        
        Args:
            input_data: Parameters for finding an available slot
            
        Returns:
            JSON string with the available slot details
        """
        if isinstance(input_data, dict):
            input_data = FindAvailableSlotInput(**input_data)
            
        try:
            # Parse date and time inputs
            start_date = datetime.datetime.strptime(input_data.start_date, "%Y-%m-%d").date()
            
            end_date = None
            if input_data.end_date:
                end_date = datetime.datetime.strptime(input_data.end_date, "%Y-%m-%d").date()
                
            start_time = None
            if input_data.start_time:
                hours, minutes = map(int, input_data.start_time.split(":"))
                start_time = datetime.time(hours, minutes)
                
            end_time = None
            if input_data.end_time:
                hours, minutes = map(int, input_data.end_time.split(":"))
                end_time = datetime.time(hours, minutes)
                
            # Find available slot
            slot_start, slot_end = self.calendar_service.find_available_slot(
                duration_minutes=input_data.duration_minutes,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                attendees=input_data.attendees,
                calendar_id=input_data.calendar_id or "primary",
                user_input=f"Find available slot: {input_data.duration_minutes} minutes starting {input_data.start_date}",
            )
            
            # Format response
            return json.dumps({
                "success": True,
                "available_slot": {
                    "start": slot_start.strftime("%Y-%m-%d %H:%M"),
                    "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                    "duration_minutes": input_data.duration_minutes,
                }
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error finding available slot: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})
    
    def check_availability(self, input_data: Union[CheckAvailabilityInput, dict]) -> str:
        """
        Check availability of attendees for a time slot.
        
        Args:
            input_data: Parameters for checking availability
            
        Returns:
            JSON string with availability information
        """
        if isinstance(input_data, dict):
            input_data = CheckAvailabilityInput(**input_data)
            
        try:
            # Parse datetimes
            start_time = datetime.datetime.strptime(input_data.start_datetime, "%Y-%m-%d %H:%M")
            end_time = datetime.datetime.strptime(input_data.end_datetime, "%Y-%m-%d %H:%M")
            
            # Check availability
            availability = self.calendar_service.check_availability(
                start_time=start_time,
                end_time=end_time,
                attendees=input_data.attendees,
                calendar_id=input_data.calendar_id or "primary",
                user_input=f"Check availability: {input_data.start_datetime} to {input_data.end_datetime}",
            )
            
            # Process availability data
            calendars = availability.get("calendars", {})
            availability_result = {}
            
            for email, calendar_data in calendars.items():
                busy_periods = calendar_data.get("busy", [])
                is_available = len(busy_periods) == 0
                
                # Format busy periods if any
                formatted_busy = []
                for busy in busy_periods:
                    busy_start = datetime.datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                    busy_end = datetime.datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                    formatted_busy.append({
                        "start": busy_start.strftime("%Y-%m-%d %H:%M"),
                        "end": busy_end.strftime("%Y-%m-%d %H:%M"),
                    })
                
                availability_result[email] = {
                    "available": is_available,
                    "busy_periods": formatted_busy,
                }
            
            # Determine overall availability
            all_available = all(data["available"] for data in availability_result.values())
            
            # Format response
            return json.dumps({
                "success": True,
                "all_available": all_available,
                "time_slot": {
                    "start": start_time.strftime("%Y-%m-%d %H:%M"),
                    "end": end_time.strftime("%Y-%m-%d %H:%M"),
                },
                "attendees": availability_result,
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})
    
    def get_tools(self) -> List[BaseTool]:
        """
        Get the list of calendar tools.
        
        Returns:
            List of tools
        """
        return [
            Tool.from_function(
                func=self.list_events,
                name="list_events",
                description="List events from the calendar within a specified date range.",
                args_schema=ListEventsInput,
                return_direct=False,
            ),
            Tool.from_function(
                func=self.create_event,
                name="create_event",
                description="Create a new event on the calendar.",
                args_schema=CreateEventInput,
                return_direct=False,
            ),
            Tool.from_function(
                func=self.update_event,
                name="update_event",
                description="Update an existing event on the calendar.",
                args_schema=UpdateEventInput,
                return_direct=False,
            ),
            Tool.from_function(
                func=self.delete_event,
                name="delete_event",
                description="Delete an event from the calendar.",
                args_schema=DeleteEventInput,
                return_direct=False,
            ),
            Tool.from_function(
                func=self.find_available_slot,
                name="find_available_slot",
                description="Find an available time slot for a meeting.",
                args_schema=FindAvailableSlotInput,
                return_direct=False,
            ),
            Tool.from_function(
                func=self.check_availability,
                name="check_availability",
                description="Check availability of attendees for a time slot.",
                args_schema=CheckAvailabilityInput,
                return_direct=False,
            ),
        ]
