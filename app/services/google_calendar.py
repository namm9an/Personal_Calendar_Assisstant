"""
Google Calendar API integration service.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, cast

from fastapi import HTTPException, status
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.models.calendar import CalendarActionCreate, CalendarActionType, CalendarProvider
from app.models.user import User
from app.schemas.calendar import (
    Event,
    EventCreate,
    EventUpdate,
    FreeSlot,
    FreeSlotRequest,
    FreeSlotResponse,
    TimeSlot,
    WorkingHours,
    EventAttendee,
)


logger = logging.getLogger(__name__)


class GoogleCalendarException(Exception):
    """Base exception for Google Calendar service errors."""
    pass


class TokenRefreshException(GoogleCalendarException):
    """Exception raised when token refresh fails."""
    pass


class GoogleCalendarClient:
    """
    Client for interacting with Google Calendar API.
    
    This class handles all interactions with the Google Calendar API, including:
    - Listing events
    - Creating events
    - Updating events
    - Deleting events
    - Finding free slots
    
    It includes retry logic with exponential backoff for API calls.
    """
    
    def __init__(self, db: Session):
        """Initialize the Google Calendar client."""
        self.db = db
        self.service_name = "calendar"
        self.version = "v3"
        self.scopes = ["https://www.googleapis.com/auth/calendar"]
        
    def _get_credentials(self, user_id: str) -> Credentials:
        """
        Get Google OAuth credentials for the user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            Credentials: The Google OAuth credentials.
            
        Raises:
            HTTPException: If the user is not found or credentials are invalid.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        if not user.google_access_token or not user.google_refresh_token:
            logger.error(f"User {user_id} has no Google credentials")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Google credentials found for user",
            )
        
        # Decrypt tokens before using
        from app.services.encryption import TokenEncryption
        encryption_service = TokenEncryption()
        
        access_token = encryption_service.decrypt(user.google_access_token)
        refresh_token = encryption_service.decrypt(user.google_refresh_token)
            
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=user.google_client_id,
            client_secret=user.google_client_secret,
            scopes=self.scopes,
        )
        
        # Refresh token if expired
        if credentials.expired:
            try:
                credentials.refresh(Request())
                # Update the user's access token in the database with encryption
                user.google_access_token = encryption_service.encrypt(credentials.token)
                self.db.commit()
            except RefreshError as e:
                logger.error(f"Failed to refresh token for user {user_id}: {str(e)}")
                self.db.rollback()
                raise TokenRefreshException(f"Failed to refresh token: {str(e)}")
            
        return credentials
    
    def _build_service(self, user_id: str):
        """
        Build the Google Calendar service for the user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            service: The Google Calendar service.
        """
        credentials = self._get_credentials(user_id)
        return build(self.service_name, self.version, credentials=credentials)
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def list_calendars(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List calendars for the user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            List[Dict[str, Any]]: List of calendars.
        """
        service = self._build_service(user_id)
        try:
            result = service.calendarList().list().execute()
            return result.get("items", [])
        except HttpError as e:
            logger.error(f"Error listing calendars for user {user_id}: {str(e)}")
            raise
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def list_events(
        self, user_id: str, time_min: datetime, time_max: datetime, calendar_id: str = "primary"
    ) -> List[Event]:
        """
        List events for the user between the specified times.
        
        Args:
            user_id: The ID of the user.
            time_min: The start time to filter events.
            time_max: The end time to filter events.
            calendar_id: The ID of the calendar (default: "primary").
            
        Returns:
            List[Event]: List of events.
        """
        service = self._build_service(user_id)
        
        # Format times for Google Calendar API
        time_min_rfc3339 = time_min.isoformat() + "Z"
        time_max_rfc3339 = time_max.isoformat() + "Z"
        
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min_rfc3339,
                timeMax=time_max_rfc3339,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            
            events = []
            for item in events_result.get("items", []):
                # Extract and convert event data
                event_id = item.get("id")
                summary = item.get("summary", "Untitled Event")
                description = item.get("description")
                location = item.get("location")
                
                # Handle different time formats (dateTime vs date)
                start = item.get("start", {})
                end = item.get("end", {})
                
                if "dateTime" in start and "dateTime" in end:
                    start_time = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
                else:
                    # All-day event
                    start_time = datetime.fromisoformat(start["date"] + "T00:00:00")
                    end_time = datetime.fromisoformat(end["date"] + "T23:59:59")
                
                time_slot = TimeSlot(start=start_time, end=end_time)
                
                # Extract other event data
                status = item.get("status")
                html_link = item.get("htmlLink")
                created = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(item["updated"].replace("Z", "+00:00"))
                organizer = item.get("organizer")
                color_id = item.get("colorId")
                
                # Convert attendees
                attendees = []
                for attendee in item.get("attendees", []):
                    attendees.append({
                        "email": attendee.get("email"),
                        "name": attendee.get("displayName"),
                        "response_status": attendee.get("responseStatus"),
                    })
                
                event = Event(
                    id=event_id,
                    summary=summary,
                    description=description,
                    location=location,
                    time_slot=time_slot,
                    attendees=attendees,
                    status=status,
                    color_id=color_id,
                    calendar_id=calendar_id,
                    html_link=html_link,
                    created=created,
                    updated=updated,
                    organizer=organizer,
                )
                events.append(event)
                
            return events
            
        except HttpError as e:
            logger.error(f"Error listing events for user {user_id}: {str(e)}")
            raise
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def create_event(self, user_id: str, event_create: EventCreate) -> Event:
        """
        Create a new event for the user.
        
        Args:
            user_id: The ID of the user.
            event_create: The event data to create.
            
        Returns:
            Event: The created event.
        """
        service = self._build_service(user_id)
        calendar_id = event_create.calendar_id or "primary"
        
        # Convert time slot to Google Calendar format
        start_time = event_create.time_slot.start
        end_time = event_create.time_slot.end
        
        # Prepare event data
        event_data = {
            "summary": event_create.summary,
            "location": event_create.location,
            "description": event_create.description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": event_create.time_zone or "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": event_create.time_zone or "UTC",
            },
            "status": event_create.status,
            "colorId": event_create.color_id,
        }
        
        # Add attendees if provided
        if event_create.attendees:
            event_data["attendees"] = [
                {"email": attendee.email, "displayName": attendee.name}
                for attendee in event_create.attendees
            ]
            
        # Add reminders if provided
        if event_create.reminders:
            event_data["reminders"] = event_create.reminders
            
        # Add conference data if provided
        if event_create.conference_data:
            event_data["conferenceData"] = event_create.conference_data
            
        try:
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event_data,
                sendUpdates="all" if event_create.send_notifications else "none",
            ).execute()
            
            # Convert response to Event model
            return self._convert_google_event_to_schema(created_event, calendar_id)
            
        except HttpError as e:
            logger.error(f"Error creating event for user {user_id}: {str(e)}")
            raise
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def update_event(
        self, user_id: str, event_id: str, event_update: EventUpdate, calendar_id: str = "primary"
    ) -> Event:
        """
        Update an existing event for the user.
        
        Args:
            user_id: The ID of the user.
            event_id: The ID of the event to update.
            event_update: The event data to update.
            calendar_id: The ID of the calendar (default: "primary").
            
        Returns:
            Event: The updated event.
        """
        service = self._build_service(user_id)
        
        # Get the current event
        try:
            current_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except HttpError as e:
            logger.error(f"Error getting event {event_id} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event not found: {event_id}",
            )
        
        # Update event fields
        event_data = {}
        
        if event_update.summary is not None:
            event_data["summary"] = event_update.summary
            
        if event_update.description is not None:
            event_data["description"] = event_update.description
            
        if event_update.location is not None:
            event_data["location"] = event_update.location
            
        if event_update.status is not None:
            event_data["status"] = event_update.status
            
        if event_update.color_id is not None:
            event_data["colorId"] = event_update.color_id
            
        # Update time slot if provided
        if event_update.time_slot:
            # Get the time zone from the current event
            start_tz = current_event.get("start", {}).get("timeZone", "UTC")
            end_tz = current_event.get("end", {}).get("timeZone", "UTC")
            
            event_data["start"] = {
                "dateTime": event_update.time_slot.start.isoformat(),
                "timeZone": start_tz,
            }
            event_data["end"] = {
                "dateTime": event_update.time_slot.end.isoformat(),
                "timeZone": end_tz,
            }
            
        # Update attendees if provided
        if event_update.attendees is not None:
            event_data["attendees"] = [
                {"email": attendee.email, "displayName": attendee.name}
                for attendee in event_update.attendees
            ]
            
        try:
            updated_event = service.events().patch(
                calendarId=calendar_id,
                eventId=event_id,
                body=event_data,
                sendUpdates="all" if event_update.send_notifications else "none",
            ).execute()
            
            # Convert response to Event model
            return self._convert_google_event_to_schema(updated_event, calendar_id)
            
        except HttpError as e:
            logger.error(f"Error updating event {event_id} for user {user_id}: {str(e)}")
            raise
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def delete_event(self, user_id: str, event_id: str, calendar_id: str = "primary") -> None:
        """
        Delete an event for the user.
        
        Args:
            user_id: The ID of the user.
            event_id: The ID of the event to delete.
            calendar_id: The ID of the calendar (default: "primary").
        """
        service = self._build_service(user_id)
        
        try:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates="all",
            ).execute()
        except HttpError as e:
            logger.error(f"Error deleting event {event_id} for user {user_id}: {str(e)}")
            raise
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def find_free_slots(
        self, user_id: str, free_slot_request: FreeSlotRequest
    ) -> FreeSlotResponse:
        """
        Find free time slots for the user based on the request criteria.
        
        Args:
            user_id: The ID of the user.
            free_slot_request: The request with criteria for finding free slots.
            
        Returns:
            FreeSlotResponse: The response with free time slots.
        """
        service = self._build_service(user_id)
        
        # Get user's timezone from database or use the one from the request
        user = self.db.query(User).filter(User.id == user_id).first()
        time_zone = user.time_zone if user else "UTC"
        
        if free_slot_request.working_hours:
            time_zone = free_slot_request.working_hours.time_zone
            
        # Get events for the date range
        events = self.list_events(
            user_id=user_id,
            time_min=free_slot_request.start_date,
            time_max=free_slot_request.end_date,
            calendar_id="primary" if not free_slot_request.calendar_ids else free_slot_request.calendar_ids[0],
        )
        
        # Convert events to busy slots
        busy_slots = [event.time_slot for event in events]
        
        # Get working hours if provided
        working_hours = free_slot_request.working_hours or self._get_default_working_hours(user)
        
        # Find free slots
        free_slots = self._find_free_slots(
            start_date=free_slot_request.start_date,
            end_date=free_slot_request.end_date,
            duration_minutes=free_slot_request.duration_minutes,
            busy_slots=busy_slots,
            working_hours=working_hours,
        )
        
        return FreeSlotResponse(slots=free_slots, time_zone=time_zone)
    
    def _get_default_working_hours(self, user: Optional[User]) -> WorkingHours:
        """
        Get the default working hours for the user.
        
        Args:
            user: The user.
            
        Returns:
            WorkingHours: The default working hours.
        """
        if user and user.working_hours:
            return WorkingHours(**user.working_hours)
        
        # Default working hours (9 AM to 5 PM, Monday to Friday)
        return WorkingHours(
            monday=(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()),
            tuesday=(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()),
            wednesday=(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()),
            thursday=(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()),
            friday=(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()),
            time_zone="UTC",
        )
    
    def _find_free_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        busy_slots: List[TimeSlot],
        working_hours: WorkingHours,
    ) -> List[FreeSlot]:
        """
        Find free time slots based on busy slots and working hours.
        
        Args:
            start_date: The start date.
            end_date: The end date.
            duration_minutes: The duration of the meeting in minutes.
            busy_slots: The list of busy time slots.
            working_hours: The working hours.
            
        Returns:
            List[FreeSlot]: The list of free time slots.
        """
        free_slots = []
        duration = timedelta(minutes=duration_minutes)
        
        # Sort busy slots by start time
        busy_slots.sort(key=lambda slot: slot.start)
        
        # Generate time slots for each day within the date range
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        while current_date <= end_day:
            # Get working hours for the current day
            day_name = current_date.strftime("%A").lower()
            day_working_hours = getattr(working_hours, day_name, None)
            
            if day_working_hours:
                # Convert working hours to datetime for the current day
                day_start = current_date.replace(
                    hour=day_working_hours[0].hour,
                    minute=day_working_hours[0].minute,
                    second=0,
                    microsecond=0,
                )
                day_end = current_date.replace(
                    hour=day_working_hours[1].hour,
                    minute=day_working_hours[1].minute,
                    second=0,
                    microsecond=0,
                )
                
                # Adjust for start_date and end_date boundaries
                if day_start < start_date:
                    day_start = start_date
                if day_end > end_date:
                    day_end = end_date
                
                # Find free slots within working hours
                if day_start < day_end:
                    # Filter busy slots for the current day
                    day_busy_slots = [
                        slot for slot in busy_slots
                        if slot.end > day_start and slot.start < day_end
                    ]
                    
                    # Initialize potential start time
                    potential_start = day_start
                    
                    # Check each potential slot
                    for busy_slot in day_busy_slots:
                        # If there's space before the busy slot
                        if potential_start + duration <= busy_slot.start:
                            free_slots.append(
                                FreeSlot(start=potential_start, end=busy_slot.start)
                            )
                        
                        # Move potential start to after the busy slot
                        potential_start = max(potential_start, busy_slot.end)
                    
                    # Check for free slot after the last busy slot
                    if potential_start + duration <= day_end:
                        free_slots.append(
                            FreeSlot(start=potential_start, end=day_end)
                        )
            
            # Move to the next day
            current_date += timedelta(days=1)
        
        return free_slots
    
    def _convert_google_event_to_schema(self, google_event: Dict[str, Any], calendar_id: str) -> Event:
        """
        Convert a Google Calendar event to an Event schema.
        
        Args:
            google_event: The Google Calendar event.
            calendar_id: The ID of the calendar.
            
        Returns:
            Event: The converted event.
        """
        # Extract event data
        event_id = google_event.get("id")
        summary = google_event.get("summary", "Untitled Event")
        description = google_event.get("description")
        location = google_event.get("location")
        
        # Handle different time formats (dateTime vs date)
        start = google_event.get("start", {})
        end = google_event.get("end", {})
        
        if "dateTime" in start and "dateTime" in end:
            start_time = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
        else:
            # All-day event
            start_time = datetime.fromisoformat(start["date"] + "T00:00:00")
            end_time = datetime.fromisoformat(end["date"] + "T23:59:59")
        
        time_slot = TimeSlot(start=start_time, end=end_time)
        
        # Extract other event data
        status = google_event.get("status")
        html_link = google_event.get("htmlLink")
        created = datetime.fromisoformat(google_event["created"].replace("Z", "+00:00"))
        updated = datetime.fromisoformat(google_event["updated"].replace("Z", "+00:00"))
        organizer = google_event.get("organizer")
        color_id = google_event.get("colorId")
        
        # Convert attendees
        attendees = []
        for attendee in google_event.get("attendees", []):
            attendees.append({
                "email": attendee.get("email"),
                "name": attendee.get("displayName"),
                "response_status": attendee.get("responseStatus"),
            })
        
        return Event(
            id=event_id,
            summary=summary,
            description=description,
            location=location,
            time_slot=time_slot,
            attendees=attendees,
            status=status,
            color_id=color_id,
            calendar_id=calendar_id,
            html_link=html_link,
            created=created,
            updated=updated,
            organizer=organizer,
        )


class GoogleCalendarService:
    """
    Service for interacting with the Google Calendar API.
    """
    
    def __init__(self, user: User, db: Session):
        """
        Initialize the Google Calendar service.
        
        Args:
            user: User for whom to perform calendar operations
            db: Database session for logging actions
        """
        self.user = user
        self.db = db
        self.client = GoogleCalendarClient(db)
        
    def _log_action(
        self,
        action_type: CalendarActionType,
        success: bool,
        user_input: Optional[str] = None,
        event_id: Optional[str] = None,
        event_summary: Optional[str] = None,
       event_start: Optional[datetime] = None,
        event_end: Optional[datetime] = None,
        provider_response: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log a calendar action to the database.
        
        Args:
            action_type: Type of calendar action
            success: Whether the action was successful
            user_input: Natural language input that triggered the action
            event_id: ID of the event (if applicable)
            event_summary: Summary of the event (if applicable)
            event_start: Start time of the event (if applicable)
            event_end: End time of the event (if applicable)
            provider_response: Response from the calendar provider
            error_message: Error message (if applicable)
        """
        try:
            calendar_action = CalendarActionCreate(
                user_id=self.user.id,
                provider=CalendarProvider.GOOGLE,
                action_type=action_type,
                event_id=event_id,
                event_summary=event_summary,
                event_start=event_start,
                event_end=event_end,
                user_input=user_input,
                provider_response=provider_response,
                success=success,
                error_message=error_message,
            )
            
            # Convert to ORM model and add to database
            from app.models.calendar import CalendarAction
            db_action = CalendarAction(**calendar_action.model_dump())
            self.db.add(db_action)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log calendar action: {str(e)}")
            # Don't raise an exception here, as this is just logging
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List calendars available to the user.
        
        Returns:
            List of calendar objects
            
        Raises:
            ValueError: If API request fails
        """
        try:
            calendars = self.client.list_calendars(self.user.id)
            self._log_action(
                action_type=CalendarActionType.LIST,
                success=True,
                provider_response={"calendars_count": len(calendars)},
            )
            return calendars
            
        except HttpError as e:
            error_message = f"Error listing calendars: {str(e)}"
            logger.error(error_message)
            
            self._log_action(
                action_type=CalendarActionType.LIST,
                success=False,
                error_message=error_message,
            )
            
            raise ValueError(error_message)
    
    def get_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
        single_events: bool = True,
        order_by: str = "startTime",
    ) -> List[Event]:
        """Get events from a calendar within a specified time range."""
        return self.client.list_events(
            user_id=self.user.id,
            time_min=time_min,
            time_max=time_max,
            calendar_id=calendar_id,
        )

    def find_free_slots(
        self,
        user_id: str,
        calendar_id: str,
        time_min: datetime,
        time_max: datetime,
        duration_minutes: int,
    ) -> List[Dict[str, Any]]:
        """Find free time slots in the calendar."""
        return self.client.find_free_slots(
            user_id=user_id,
            free_slot_request=FreeSlotRequest(
                start_date=time_min,
                end_date=time_max,
                duration_minutes=duration_minutes,
                calendar_ids=[calendar_id] if calendar_id != "primary" else None,
            )
        ).slots

    def create_event(
        self,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[Dict[str, str]]] = None, # Format: [{'email': '...', 'name': '...'}]
        time_zone: Optional[str] = None,
        conference_data: Optional[Dict[str, Any]] = None,
        user_input: Optional[str] = None, # For logging
    ) -> Dict[str, Any]:
        """
        Create a new event in Google Calendar.
        
        Args:
            summary: Title of the event.
            start_datetime: Start date and time of the event.
            end_datetime: End date and time of the event.
            calendar_id: Calendar ID to create the event in.
            description: Description of the event.
            location: Location of the event.
            attendees: List of attendees (email and name).
            time_zone: Timezone for the event (e.g., 'America/Los_Angeles'). Defaults to user's timezone or UTC.
            conference_data: Conference data for the event.
            user_input: Original user input string for logging.
            
        Returns:
            A dictionary representing the created event, usually from the client.
        """
        try:
            user_timezone = time_zone or self.user.timezone or "UTC"
            
            # Prepare attendees in the format expected by EventCreate schema
            formatted_attendees: Optional[List[EventAttendee]] = None
            if attendees:
                formatted_attendees = []
                for att_data in attendees:
                    # EventCreate.attendees expects a list of EventAttendee Pydantic models
                    formatted_attendees.append(EventAttendee(
                        email=att_data.get("email"),
                        name=att_data.get("displayName") or att_data.get("name")
                        # response_status can be added if available/needed
                    ))

            event_create_payload = EventCreate(
                summary=summary,
                time_slot=TimeSlot(start=start_datetime, end=end_datetime),
                calendar_id=calendar_id,
                description=description,
                location=location,
                attendees=formatted_attendees if formatted_attendees else None, # Pass None if empty, not an empty list for some APIs
                time_zone=user_timezone,
                conference_data=conference_data,
                send_notifications=True # Default to sending notifications, can be made configurable
                # status, color_id, reminders can be added if needed
            )
            
            logger.info(f"Creating event for user {self.user.id} in calendar {calendar_id}: {summary}")
            
            created_event_data = self.client.create_event(
                user_id=str(self.user.id),
                event_create=event_create_payload
            )
            
            # The client's create_event returns an Event Pydantic model.
            # We should convert it to a dict if the service layer is expected to return dicts.
            # Or, adjust the return type annotation of this service method to -> Event.
            # For now, assuming client returns a Pydantic model and we convert to dict.
            
            # Log the action
            self._log_action(
                action_type=CalendarActionType.CREATE_EVENT,
                success=True,
                user_input=user_input or f"Create event: {summary}",
                event_id=created_event_data.id, # Assuming Event model has an 'id'
                event_summary=summary,
                event_start=start_datetime,
                event_end=end_datetime,
                calendar_id=calendar_id,
                provider_response=created_event_data.model_dump_json() # Log the Pydantic model as JSON
            )
            
            return created_event_data.model_dump() # Return as dict

        except HTTPException: # Re-raise HTTPException to be caught by FastAPI layer
            raise
        except Exception as e:
            logger.error(
                f"Error in GoogleCalendarService.create_event for user {self.user.id}: {str(e)}",
                exc_info=True
            )
            self._log_action(
                action_type=CalendarActionType.CREATE_EVENT,
                success=False,
                user_input=user_input or f"Create event: {summary}",
                error_message=str(e),
                calendar_id=calendar_id,
            )
            # Convert general exceptions to a standard service layer exception or HTTPException
            raise GoogleCalendarException(f"Failed to create event: {str(e)}") from e

    def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[Dict[str, str]]] = None,
        user_input: Optional[str] = None,
    ) -> Event:
        """
        Update an existing event on the calendar.
        
        Args:
            event_id: ID of the event to update
            calendar_id: ID of the calendar (default: "primary")
            summary: New event title (if changing)
            start_time: New start time (if changing)
            end_time: New end time (if changing)
            description: New description (if changing)
            location: New location (if changing)
            attendees: New list of attendees (if changing)
            user_input: Natural language input that triggered this action
            
        Returns:
            Updated event object
            
        Raises:
            ValueError: If API request fails
        """
        event_update = EventUpdate(
            summary=summary,
            time_slot=TimeSlot(start=start_time, end=end_time) if start_time or end_time else None,
            description=description,
            location=location,
            attendees=attendees,
        )
        
        try:
            updated_event = self.client.update_event(
                user_id=self.user.id,
                event_id=event_id,
                event_update=event_update,
                calendar_id=calendar_id,
            )
            self._log_action(
                action_type=CalendarActionType.UPDATE,
                success=True,
                user_input=user_input,
                event_id=updated_event.id,
                event_summary=updated_event.summary,
                event_start=updated_event.time_slot.start,
                event_end=updated_event.time_slot.end,
                provider_response=updated_event,
            )
            return updated_event
            
        except HttpError as e:
            error_message = f"Error updating event: {str(e)}"
            logger.error(error_message)
            
            self._log_action(
                action_type=CalendarActionType.UPDATE,
                success=False,
                user_input=user_input,
                event_id=event_id,
                error_message=error_message,
            )
            
            raise ValueError(error_message)
    
    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> bool:
        """
        Delete an event from the calendar.
        
        Args:
            event_id: ID of the event to delete
            calendar_id: ID of the calendar (default: "primary")
            user_input: Natural language input that triggered this action
            
        Returns:
            True if deletion was successful
            
        Raises:
            ValueError: If API request fails
        """
        try:
            self.client.delete_event(self.user.id, event_id, calendar_id)
            self._log_action(
                action_type=CalendarActionType.DELETE,
                success=True,
                user_input=user_input,
                event_id=event_id,
                provider_response={"deleted": True},
            )
            return True
            
        except HttpError as e:
            error_message = f"Error deleting event: {str(e)}"
            logger.error(error_message)
            
            self._log_action(
                action_type=CalendarActionType.DELETE,
                success=False,
                user_input=user_input,
                event_id=event_id,
                error_message=error_message,
            )
            
            raise ValueError(error_message)
    
    def check_availability(
        self,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check availability of attendees for a time slot.
        
        Args:
            start_time: Start time to check
            end_time: End time to check
            attendees: List of attendee emails
            calendar_id: ID of the calendar (default: "primary")
            user_input: Natural language input that triggered this action
            
        Returns:
            Availability information
            
        Raises:
            ValueError: If API request fails
        """
        try:
            # Create FreeBusy request
            freebusy_request = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "timeZone": self.user.timezone,
                "items": [{"id": email} for email in attendees],
            }
            
            # Add the user's calendar
            freebusy_request["items"].append({"id": calendar_id})
            
            # Make the FreeBusy query
            freebusy_response = self.client.service.freebusy().query(
                body=freebusy_request
            ).execute()
            
            self._log_action(
                action_type=CalendarActionType.AVAILABILITY,
                success=True,
                user_input=user_input,
                event_start=start_time,
                event_end=end_time,
                provider_response=freebusy_response,
            )
            
            return freebusy_response
            
        except HttpError as e:
            error_message = f"Error checking availability: {str(e)}"
            logger.error(error_message)
            
            self._log_action(
                action_type=CalendarActionType.AVAILABILITY,
                success=False,
                user_input=user_input,
                event_start=start_time,
                event_end=end_time,
                error_message=error_message,
            )
            
            raise ValueError(error_message)
    
    def find_available_slot(
        self,
        duration_minutes: int,
        start_date: datetime.date,
        end_date: Optional[datetime.date] = None,
        start_time: Optional[datetime.time] = None,
        end_time: Optional[datetime.time] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> Tuple[datetime, datetime]:
        """
        Find an available time slot for a meeting.
        
        Args:
            duration_minutes: Duration of the meeting in minutes
            start_date: Start date to search from
            end_date: End date to search until (default: start_date + 1 day)
            start_time: Earliest time of day to consider (default: user's working hours start)
            end_time: Latest time of day to consider (default: user's working hours end)
            attendees: List of attendee emails (default: None, just check user's calendar)
            calendar_id: ID of the calendar (default: "primary")
            user_input: Natural language input that triggered this action
            
        Returns:
            Tuple of (start_time, end_time) for the available slot
            
        Raises:
            ValueError: If no available slot is found or API request fails
        """
        # Set default values
        if end_date is None:
            end_date = start_date + datetime.timedelta(days=1)
            
        if start_time is None:
            start_time = self.user.working_hours_start
            
        if end_time is None:
            end_time = self.user.working_hours_end
            
        if attendees is None:
            attendees = []
            
        # Prepare dates for search
        current_date = start_date
        
        while current_date <= end_date:
            # Combine date and time for start and end of workday
            day_start = datetime.combine(
                current_date, start_time, tzinfo=datetime.timezone.utc
            )
            day_end = datetime.combine(
                current_date, end_time, tzinfo=datetime.timezone.utc
            )
            
            # Adjust for current time if searching today
            now = datetime.now(datetime.timezone.utc)
            if current_date == now.date() and day_start < now:
                day_start = now
                
            # Check if we still have enough time today
            if (day_end - day_start).total_seconds() < duration_minutes * 60:
                current_date += datetime.timedelta(days=1)
                continue
                
            # Get events for this day
            try:
                events = self.get_events(
                    calendar_id=calendar_id,
                    time_min=day_start,
                    time_max=day_end,
                    max_results=50,
                )
                
                # Check availability if attendees are specified
                if attendees:
                    availability = self.check_availability(
                        start_time=day_start,
                        end_time=day_end,
                        attendees=attendees,
                        calendar_id=calendar_id,
                        user_input=user_input,
                    )
                    
                    # Process availability data
                    busy_periods = []
                    
                    # Add user's busy periods
                    for calendar, calendar_data in availability.get("calendars", {}).items():
                        for busy in calendar_data.get("busy", []):
                            start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                            end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                            busy_periods.append((start, end))
                else:
                    # Just use events from the user's calendar
                    busy_periods = []
                    for event in events:
                        if event.get("status") not in ["cancelled"]:
                            start = event.get("start", {})
                            end = event.get("end", {})
                            
                            # Handle all-day events
                            if "dateTime" in start and "dateTime" in end:
                                start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                                end_dt = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
                                busy_periods.append((start_dt, end_dt))
                
                # Sort busy periods by start time
                busy_periods.sort(key=lambda x: x[0])
                
                # Find gaps between busy periods
                if not busy_periods:
                    # No busy periods, entire day is available
                    slot_start = day_start
                    slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)
                    
                    if slot_end <= day_end:
                        self._log_action(
                            action_type=CalendarActionType.AVAILABILITY,
                            success=True,
                            user_input=user_input,
                            event_start=slot_start,
                            event_end=slot_end,
                            provider_response={"found_slot": True},
                        )
                        
                        return slot_start, slot_end
                else:
                    # Check for gap at the beginning of the day
                    if (busy_periods[0][0] - day_start).total_seconds() >= duration_minutes * 60:
                        slot_start = day_start
                        slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)
                        
                        self._log_action(
                            action_type=CalendarActionType.AVAILABILITY,
                            success=True,
                            user_input=user_input,
                            event_start=slot_start,
                            event_end=slot_end,
                            provider_response={"found_slot": True},
                        )
                        
                        return slot_start, slot_end
                    
                    # Check for gaps between busy periods
                    for i in range(len(busy_periods) - 1):
                        gap_start = busy_periods[i][1]
                        gap_end = busy_periods[i + 1][0]
                        
                        if (gap_end - gap_start).total_seconds() >= duration_minutes * 60:
                            slot_start = gap_start
                            slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)
                            
                            self._log_action(
                                action_type=CalendarActionType.AVAILABILITY,
                                success=True,
                                user_input=user_input,
                                event_start=slot_start,
                                event_end=slot_end,
                                provider_response={"found_slot": True},
                            )
                            
                            return slot_start, slot_end
                    
                    # Check for gap at the end of the day
                    if (day_end - busy_periods[-1][1]).total_seconds() >= duration_minutes * 60:
                        slot_start = busy_periods[-1][1]
                        slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)
                        
                        if slot_end <= day_end:
                            self._log_action(
                                action_type=CalendarActionType.AVAILABILITY,
                                success=True,
                                user_input=user_input,
                                event_start=slot_start,
                                event_end=slot_end,
                                provider_response={"found_slot": True},
                            )
                            
                            return slot_start, slot_end
                
            except Exception as e:
                logger.error(f"Error finding available slot on {current_date}: {str(e)}")
                # Continue to next day
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        # No available slot found
        self._log_action(
            action_type=CalendarActionType.AVAILABILITY,
            success=False,
            user_input=user_input,
            error_message="No available slot found",
        )
        
        raise ValueError(f"No available slot found for {duration_minutes} minutes between {start_date} and {end_date} during working hours")

    async def list_events(self, *args, **kwargs):
        raise NotImplementedError("Stub method for tests.")

    async def create_event(self, *args, **kwargs):
        raise NotImplementedError("Stub method for tests.")

    async def update_event(self, *args, **kwargs):
        raise NotImplementedError("Stub method for tests.")

    async def delete_event(self, *args, **kwargs):
        raise NotImplementedError("Stub method for tests.")

    # Add any additional stubs as needed for test coverage
