"""
Microsoft Calendar service for interacting with Microsoft Graph API.
"""
import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple, cast

import requests
from fastapi import HTTPException, status
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
from app.schemas.ms_calendar import (
    MSCalendarEvent,
    MSCalendarCreate,
    MSCalendarUpdate,
    MSFreeSlotRequest,
    MSFreeSlotResponse,
    MSTimeSlot,
)
from app.services.ms_oauth import MicrosoftOAuthService

logger = logging.getLogger(__name__)


class MicrosoftGraphException(Exception):
    """Base exception for Microsoft Graph API errors."""
    pass


class MicrosoftGraphRateLimitException(MicrosoftGraphException):
    """Exception raised when rate limited by Microsoft Graph API."""
    pass


class MicrosoftCalendarService:
    """
    Service for interacting with Microsoft Calendar via Graph API.
    
    This class handles all interactions with the Microsoft Calendar API, including:
    - Listing events
    - Creating events
    - Updating events
    - Deleting events
    - Finding free slots
    
    It includes retry logic with exponential backoff for API calls.
    """
    
    def __init__(self, user: User, db: Session):
        """
        Initialize the Microsoft Calendar service.
        
        Args:
            user: User for whom to perform calendar operations
            db: Database session for logging actions
        """
        self.user = user
        self.db = db
        self.ms_oauth_service = MicrosoftOAuthService(db)
        self.base_url = "https://graph.microsoft.com/v1.0"
        
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
            action_type: Type of action performed
            success: Whether the action was successful
            user_input: Optional user input that triggered the action
            event_id: Optional ID of the event
            event_summary: Optional summary/title of the event
            event_start: Optional start time of the event
            event_end: Optional end time of the event
            provider_response: Optional raw response from the provider
            error_message: Optional error message if the action failed
        """
        try:
            action = CalendarActionCreate(
                user_id=self.user.id,
                provider=CalendarProvider.MICROSOFT,
                action_type=action_type,
                success=success,
                user_input=user_input,
                event_id=event_id,
                event_summary=event_summary,
                event_start=event_start,
                event_end=event_end,
                provider_response=provider_response,
                error_message=error_message,
            )
            
            from app.models.calendar import CalendarAction
            
            db_action = CalendarAction(**action.model_dump())
            self.db.add(db_action)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging calendar action: {str(e)}")
            self.db.rollback()

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Microsoft Graph API requests including access token.
        
        Returns:
            Dict with authorization header
        """
        access_token, _, _ = self.ms_oauth_service.get_tokens(str(self.user.id))
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
    
    @retry(
        retry=retry_if_exception_type(MicrosoftGraphRateLimitException),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the Microsoft Graph API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            params: Optional query parameters
            data: Optional request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            HTTPException: If request fails
            MicrosoftGraphRateLimitException: If rate limited (will be retried)
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, params=params, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logger.warning(f"Rate limited by Microsoft Graph API. Retry after {retry_after} seconds.")
                raise MicrosoftGraphRateLimitException(f"Rate limited. Retry after {retry_after} seconds.")
            
            # Handle other errors
            if not response.ok:
                error_data = response.json() if response.content else {"error": "Unknown error"}
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Microsoft Graph API error: {error_message}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Microsoft Graph API error: {error_message}",
                )
            
            # Return response data
            if response.content:
                return response.json()
            return {}
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Request error: {str(e)}",
            )
    
    def list_events_ms(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
        order_by: str = "start/dateTime",
    ) -> List[MSCalendarEvent]:
        """
        List events from Microsoft Calendar.
        
        Args:
            calendar_id: Calendar ID (default "primary")
            time_min: Start time for filtering events
            time_max: End time for filtering events
            max_results: Maximum number of events to return
            order_by: Field to order results by
            
        Returns:
            List of calendar events
        """
        if time_min is None:
            time_min = datetime.utcnow()
            
        if time_max is None:
            time_max = time_min + timedelta(days=7)
        
        # Format datetime parameters
        start_datetime = time_min.isoformat() + 'Z'
        end_datetime = time_max.isoformat() + 'Z'
        
        # Build query parameters
        params = {
            "$top": max_results,
            "$orderby": order_by,
            "$filter": f"start/dateTime ge '{start_datetime}' and end/dateTime le '{end_datetime}'",
        }
        
        # Determine endpoint based on calendar ID
        endpoint = "/me/events" if calendar_id == "primary" else f"/me/calendars/{calendar_id}/events"
        
        try:
            response = self._make_request(method="GET", endpoint=endpoint, params=params)
            
            events = []
            for item in response.get("value", []):
                # Convert Microsoft format to our schema
                event = MSCalendarEvent(
                    id=item.get("id"),
                    summary=item.get("subject", ""),
                    description=item.get("bodyPreview", ""),
                    location=item.get("location", {}).get("displayName", ""),
                    start=datetime.fromisoformat(item.get("start", {}).get("dateTime").replace('Z', '+00:00')),
                    end=datetime.fromisoformat(item.get("end", {}).get("dateTime").replace('Z', '+00:00')),
                    is_all_day=item.get("isAllDay", False),
                    attendees=[
                        {"email": attendee.get("emailAddress", {}).get("address", ""), 
                         "name": attendee.get("emailAddress", {}).get("name", "")}
                        for attendee in item.get("attendees", [])
                    ],
                    organizer={
                        "email": item.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                        "name": item.get("organizer", {}).get("emailAddress", {}).get("name", ""),
                    },
                    created=datetime.fromisoformat(item.get("createdDateTime").replace('Z', '+00:00')) if item.get("createdDateTime") else None,
                    updated=datetime.fromisoformat(item.get("lastModifiedDateTime").replace('Z', '+00:00')) if item.get("lastModifiedDateTime") else None,
                    status=item.get("showAs", ""),
                    recurrence=item.get("recurrence"),
                    web_link=item.get("webLink", ""),
                )
                events.append(event)
            
            # Log successful action
            self._log_action(
                action_type=CalendarActionType.LIST_EVENTS,
                success=True,
                event_start=time_min,
                event_end=time_max,
                provider_response=response,
            )
            
            return events
            
        except Exception as e:
            # Log failed action
            self._log_action(
                action_type=CalendarActionType.LIST_EVENTS,
                success=False,
                event_start=time_min,
                event_end=time_max,
                error_message=str(e),
            )
            raise
    
    def create_event_ms(
        self,
        event_data: MSCalendarCreate,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> MSCalendarEvent:
        """
        Create a new event in Microsoft Calendar.
        
        Args:
            event_data: Event data
            calendar_id: Calendar ID (default "primary")
            user_input: Optional user input that triggered the action
            
        Returns:
            Created event
        """
        # Format datetime parameters
        start_datetime = event_data.start.isoformat()
        end_datetime = event_data.end.isoformat()
        
        # Build attendees list if provided
        attendees = None
        if event_data.attendees:
            attendees = [
                {
                    "emailAddress": {
                        "address": attendee.get("email", ""),
                        "name": attendee.get("name", ""),
                    },
                    "type": "required",
                }
                for attendee in event_data.attendees
            ]
        
        # Build request body
        event_body = {
            "subject": event_data.summary,
            "body": {
                "contentType": "text",
                "content": event_data.description or "",
            },
            "start": {
                "dateTime": start_datetime,
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "UTC",
            },
            "isAllDay": event_data.is_all_day or False,
        }
        
        if event_data.location:
            event_body["location"] = {
                "displayName": event_data.location,
            }
            
        if attendees:
            event_body["attendees"] = attendees
        
        # Determine endpoint based on calendar ID
        endpoint = "/me/events" if calendar_id == "primary" else f"/me/calendars/{calendar_id}/events"
        
        try:
            response = self._make_request(method="POST", endpoint=endpoint, data=event_body)
            
            # Convert response to our schema
            created_event = MSCalendarEvent(
                id=response.get("id"),
                summary=response.get("subject", ""),
                description=response.get("bodyPreview", ""),
                location=response.get("location", {}).get("displayName", ""),
                start=datetime.fromisoformat(response.get("start", {}).get("dateTime").replace('Z', '+00:00')),
                end=datetime.fromisoformat(response.get("end", {}).get("dateTime").replace('Z', '+00:00')),
                is_all_day=response.get("isAllDay", False),
                attendees=[
                    {"email": attendee.get("emailAddress", {}).get("address", ""), 
                     "name": attendee.get("emailAddress", {}).get("name", "")}
                    for attendee in response.get("attendees", [])
                ],
                organizer={
                    "email": response.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                    "name": response.get("organizer", {}).get("emailAddress", {}).get("name", ""),
                },
                created=datetime.fromisoformat(response.get("createdDateTime").replace('Z', '+00:00')) if response.get("createdDateTime") else None,
                updated=datetime.fromisoformat(response.get("lastModifiedDateTime").replace('Z', '+00:00')) if response.get("lastModifiedDateTime") else None,
                status=response.get("showAs", ""),
                recurrence=response.get("recurrence"),
                web_link=response.get("webLink", ""),
            )
            
            # Log successful action
            self._log_action(
                action_type=CalendarActionType.CREATE_EVENT,
                success=True,
                user_input=user_input,
                event_id=created_event.id,
                event_summary=created_event.summary,
                event_start=created_event.start,
                event_end=created_event.end,
                provider_response=response,
            )
            
            return created_event
            
        except Exception as e:
            # Log failed action
            self._log_action(
                action_type=CalendarActionType.CREATE_EVENT,
                success=False,
                user_input=user_input,
                event_summary=event_data.summary,
                event_start=event_data.start,
                event_end=event_data.end,
                error_message=str(e),
            )
            raise
    
    def update_event_ms(
        self,
        event_id: str,
        event_data: MSCalendarUpdate,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> MSCalendarEvent:
        """
        Update an existing event in Microsoft Calendar.
        
        Args:
            event_id: ID of the event to update
            event_data: Updated event data
            calendar_id: Calendar ID (default "primary")
            user_input: Optional user input that triggered the action
            
        Returns:
            Updated event
        """
        # Build request body with only fields that are provided
        event_body = {}
        
        if event_data.summary is not None:
            event_body["subject"] = event_data.summary
            
        if event_data.description is not None:
            event_body["body"] = {
                "contentType": "text",
                "content": event_data.description,
            }
            
        if event_data.location is not None:
            event_body["location"] = {
                "displayName": event_data.location,
            }
            
        if event_data.start is not None:
            event_body["start"] = {
                "dateTime": event_data.start.isoformat(),
                "timeZone": "UTC",
            }
            
        if event_data.end is not None:
            event_body["end"] = {
                "dateTime": event_data.end.isoformat(),
                "timeZone": "UTC",
            }
            
        if event_data.is_all_day is not None:
            event_body["isAllDay"] = event_data.is_all_day
            
        if event_data.attendees is not None:
            event_body["attendees"] = [
                {
                    "emailAddress": {
                        "address": attendee.get("email", ""),
                        "name": attendee.get("name", ""),
                    },
                    "type": "required",
                }
                for attendee in event_data.attendees
            ]
        
        # Determine endpoint based on calendar ID
        endpoint = f"/me/events/{event_id}" if calendar_id == "primary" else f"/me/calendars/{calendar_id}/events/{event_id}"
        
        try:
            # Patch request to update only provided fields
            response = self._make_request(method="PATCH", endpoint=endpoint, data=event_body)
            
            # Get the updated event
            updated_response = self._make_request(method="GET", endpoint=endpoint)
            
            # Convert response to our schema
            updated_event = MSCalendarEvent(
                id=updated_response.get("id"),
                summary=updated_response.get("subject", ""),
                description=updated_response.get("bodyPreview", ""),
                location=updated_response.get("location", {}).get("displayName", ""),
                start=datetime.fromisoformat(updated_response.get("start", {}).get("dateTime").replace('Z', '+00:00')),
                end=datetime.fromisoformat(updated_response.get("end", {}).get("dateTime").replace('Z', '+00:00')),
                is_all_day=updated_response.get("isAllDay", False),
                attendees=[
                    {"email": attendee.get("emailAddress", {}).get("address", ""), 
                     "name": attendee.get("emailAddress", {}).get("name", "")}
                    for attendee in updated_response.get("attendees", [])
                ],
                organizer={
                    "email": updated_response.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                    "name": updated_response.get("organizer", {}).get("emailAddress", {}).get("name", ""),
                },
                created=datetime.fromisoformat(updated_response.get("createdDateTime").replace('Z', '+00:00')) if updated_response.get("createdDateTime") else None,
                updated=datetime.fromisoformat(updated_response.get("lastModifiedDateTime").replace('Z', '+00:00')) if updated_response.get("lastModifiedDateTime") else None,
                status=updated_response.get("showAs", ""),
                recurrence=updated_response.get("recurrence"),
                web_link=updated_response.get("webLink", ""),
            )
            
            # Log successful action
            self._log_action(
                action_type=CalendarActionType.UPDATE_EVENT,
                success=True,
                user_input=user_input,
                event_id=updated_event.id,
                event_summary=updated_event.summary,
                event_start=updated_event.start,
                event_end=updated_event.end,
                provider_response=updated_response,
            )
            
            return updated_event
            
        except Exception as e:
            # Log failed action
            self._log_action(
                action_type=CalendarActionType.UPDATE_EVENT,
                success=False,
                user_input=user_input,
                event_id=event_id,
                error_message=str(e),
            )
            raise
    
    def delete_event_ms(
        self,
        event_id: str,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> bool:
        """
        Delete an event from Microsoft Calendar.
        
        Args:
            event_id: ID of the event to delete
            calendar_id: Calendar ID (default "primary")
            user_input: Optional user input that triggered the action
            
        Returns:
            True if successful
        """
        # Get event details before deletion for logging
        endpoint = f"/me/events/{event_id}" if calendar_id == "primary" else f"/me/calendars/{calendar_id}/events/{event_id}"
        
        try:
            # Get event details
            event_response = self._make_request(method="GET", endpoint=endpoint)
            
            event_summary = event_response.get("subject", "")
            event_start = datetime.fromisoformat(event_response.get("start", {}).get("dateTime").replace('Z', '+00:00')) if event_response.get("start", {}).get("dateTime") else None
            event_end = datetime.fromisoformat(event_response.get("end", {}).get("dateTime").replace('Z', '+00:00')) if event_response.get("end", {}).get("dateTime") else None
            
            # Delete the event
            self._make_request(method="DELETE", endpoint=endpoint)
            
            # Log successful action
            self._log_action(
                action_type=CalendarActionType.DELETE_EVENT,
                success=True,
                user_input=user_input,
                event_id=event_id,
                event_summary=event_summary,
                event_start=event_start,
                event_end=event_end,
            )
            
            return True
            
        except Exception as e:
            # Log failed action
            self._log_action(
                action_type=CalendarActionType.DELETE_EVENT,
                success=False,
                user_input=user_input,
                event_id=event_id,
                error_message=str(e),
            )
            raise
    
    def find_free_slots_ms(
        self,
        duration_minutes: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> List[MSTimeSlot]:
        """
        Find available time slots for a meeting.
        
        Args:
            duration_minutes: Duration of the meeting in minutes
            start_date: Start date for the search range (default: now)
            end_date: End date for the search range (default: start_date + 7 days)
            attendees: Optional list of attendee email addresses
            calendar_id: Calendar ID (default "primary")
            user_input: Optional user input that triggered the action
            
        Returns:
            List of available time slots
        """
        if start_date is None:
            start_date = datetime.utcnow()
            
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        
        # Get user's working hours
        working_hours_start = self.user.working_hours_start or time(9, 0)
        working_hours_end = self.user.working_hours_end or time(17, 0)
        
        # Prepare attendees for the scheduling API
        schedules = ["me"]
        if attendees:
            schedules.extend(attendees)
        
        # Format dates for API
        start_datetime = start_date.isoformat() + 'Z'
        end_datetime = end_date.isoformat() + 'Z'
        
        # Request body for finding availability
        request_body = {
            "schedules": schedules,
            "startTime": {
                "dateTime": start_datetime,
                "timeZone": "UTC"
            },
            "endTime": {
                "dateTime": end_datetime,
                "timeZone": "UTC"
            },
            "availabilityViewInterval": 30  # 30-minute intervals
        }
        
        try:
            # Call Microsoft Graph API to get availability
            response = self._make_request(
                method="POST",
                endpoint="/me/calendar/getSchedule",
                data=request_body
            )
            
            # Process the response to find free slots
            free_slots = []
            schedule_items = response.get("value", [])
            
            # Process each day in the range
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                # Combine date with working hours
                day_start = datetime.combine(current_date, working_hours_start, tzinfo=datetime.timezone.utc)
                day_end = datetime.combine(current_date, working_hours_end, tzinfo=datetime.timezone.utc)
                
                # Adjust for current time (don't suggest slots in the past)
                now = datetime.now(datetime.timezone.utc)
                if current_date == now.date() and day_start < now:
                    day_start = now
                
                # Skip if day_start is after day_end (happens if now is after working hours)
                if day_start >= day_end:
                    current_date += timedelta(days=1)
                    continue
                
                # Get busy periods for all attendees on this day
                busy_periods = []
                
                for schedule in schedule_items:
                    # Skip if no working hours or availability info
                    if "availabilityView" not in schedule:
                        continue
                    
                    availability_view = schedule.get("availabilityView", "")
                    working_hours = schedule.get("workingHours", {})
                    
                    # If working hours are defined, use them
                    if working_hours:
                        # Extract working hours start and end times
                        start_time_str = working_hours.get("startTime", "09:00:00.0000000")
                        end_time_str = working_hours.get("endTime", "17:00:00.0000000")
                        
                        # Parse times
                        hours_start = datetime.strptime(start_time_str.split('.')[0], "%H:%M:%S").time()
                        hours_end = datetime.strptime(end_time_str.split('.')[0], "%H:%M:%S").time()
                        
                        # Combine with current date
                        person_day_start = datetime.combine(current_date, hours_start, tzinfo=datetime.timezone.utc)
                        person_day_end = datetime.combine(current_date, hours_end, tzinfo=datetime.timezone.utc)
                        
                        # Adjust working hours
                        if person_day_start > day_start:
                            day_start = person_day_start
                        if person_day_end < day_end:
                            day_end = person_day_end
                    
                    # Process scheduled events
                    for event in schedule.get("scheduleItems", []):
                        # Only process events on the current day
                        event_start = datetime.fromisoformat(event.get("start", {}).get("dateTime").replace('Z', '+00:00'))
                        event_end = datetime.fromisoformat(event.get("end", {}).get("dateTime").replace('Z', '+00:00'))
                        
                        # Check if event is on the current day
                        if event_start.date() <= current_date <= event_end.date():
                            # Add to busy periods if event overlaps with working hours
                            if event_end > day_start and event_start < day_end:
                                busy_start = max(event_start, day_start)
                                busy_end = min(event_end, day_end)
                                busy_periods.append((busy_start, busy_end))
                
                # Sort busy periods by start time
                busy_periods.sort(key=lambda x: x[0])
                
                # Merge overlapping busy periods
                merged_busy = []
                for period in busy_periods:
                    if not merged_busy or period[0] > merged_busy[-1][1]:
                        merged_busy.append(period)
                    else:
                        merged_busy[-1] = (merged_busy[-1][0], max(merged_busy[-1][1], period[1]))
                
                # Find free slots between busy periods
                free_start = day_start
                for busy_start, busy_end in merged_busy:
                    # If there's a gap before this busy period
                    if free_start + timedelta(minutes=duration_minutes) <= busy_start:
                        # Add free slot
                        free_slots.append(
                            MSTimeSlot(
                                start=free_start,
                                end=free_start + timedelta(minutes=duration_minutes),
                            )
                        )
                    # Move free_start to after this busy period
                    free_start = busy_end
                
                # Check if there's a slot after the last busy period
                if free_start + timedelta(minutes=duration_minutes) <= day_end:
                    free_slots.append(
                        MSTimeSlot(
                            start=free_start,
                            end=free_start + timedelta(minutes=duration_minutes),
                        )
                    )
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Log successful action
            self._log_action(
                action_type=CalendarActionType.FIND_FREE_SLOTS,
                success=True,
                user_input=user_input,
                event_start=start_date,
                event_end=end_date,
                provider_response=response,
            )
            
            return free_slots[:10]  # Return top 10 slots
            
        except Exception as e:
            # Log failed action
            self._log_action(
                action_type=CalendarActionType.FIND_FREE_SLOTS,
                success=False,
                user_input=user_input,
                event_start=start_date,
                event_end=end_date,
                error_message=str(e),
            )
            raise


class MicrosoftCalendarClient:
    """
    Client wrapper for Microsoft Calendar service (Phase 2).
    This class provides the interface that the API routes expect.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Microsoft Calendar client.
        
        Args:
            db: Database session
        """
        self.db = db
        # Service will be initialized when a user is provided
        self.service = None
    
    def _init_service(self, user_id: str) -> MicrosoftCalendarService:
        """Initialize the service with a user"""
        from app.models.user import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        self.service = MicrosoftCalendarService(user, self.db)
        return self.service
    
    def list_calendars(self, user_id: str):
        """List all calendars for the user"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
    
    def list_events(
        self,
        user_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        calendar_id: str = "primary",
        max_results: int = 10,
    ):
        """List events for the user"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
    
    def create_event(
        self,
        user_id: str,
        event_data: Any,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ):
        """Create a new event"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
    
    def get_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary",
    ):
        """Get a specific event"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
    
    def update_event(
        self,
        user_id: str,
        event_id: str,
        event_data: Any,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ):
        """Update an existing event"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
    
    def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ):
        """Delete an event"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
    
    def find_free_slots(
        self,
        user_id: str,
        request: Any,
    ):
        """Find free time slots"""
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration is planned for Phase 2",
        )
