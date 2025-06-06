"""
Microsoft Calendar service for interacting with Microsoft Graph API.
"""
import logging
from datetime import datetime, time, timedelta, timezone
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
from app.core.exceptions import CalendarError, OAuthError

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
            
        Raises:
            OAuthError: If token retrieval fails
        """
        try:
            access_token, _, _ = self.ms_oauth_service.get_tokens(str(self.user.id))
            return {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        except Exception as e:
            raise OAuthError(f"Failed to get access token: {str(e)}", provider="microsoft", original_exception=e)
    
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
            CalendarError: If request fails
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
                raise CalendarError(f"Microsoft Graph API error: {error_message}")
            
            # Return response data
            if response.content:
                return response.json()
            return {}
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise CalendarError(f"Request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise CalendarError(f"Unexpected error: {str(e)}")

    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars for the user.
        
        Returns:
            List of calendar objects
            
        Raises:
            CalendarError: If calendar listing fails
        """
        try:
            response = self._make_request("GET", "/me/calendars")
            return response.get("value", [])
        except Exception as e:
            self._log_action(
                action_type=CalendarActionType.LIST_CALENDARS,
                success=False,
                error_message=str(e)
            )
            raise CalendarError(f"Failed to list calendars: {str(e)}")

    def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
        order_by: str = "start/dateTime",
    ) -> List[Dict[str, Any]]:
        """
        List events from the specified calendar.
        
        Args:
            calendar_id: Calendar ID (default: "primary")
            time_min: Start time for events
            time_max: End time for events
            max_results: Maximum number of events to return
            order_by: Field to order results by
            
        Returns:
            List of event objects
            
        Raises:
            CalendarError: If event listing fails
        """
        try:
            params = {
                "$top": max_results,
                "$orderby": order_by,
            }
            
            if time_min:
                params["startDateTime"] = time_min.isoformat()
            if time_max:
                params["endDateTime"] = time_max.isoformat()
            
            response = self._make_request(
                "GET",
                f"/me/calendars/{calendar_id}/events",
                params=params
            )
            
            self._log_action(
                action_type=CalendarActionType.LIST_EVENTS,
                success=True
            )
            
            return response.get("value", [])
        except Exception as e:
            self._log_action(
                action_type=CalendarActionType.LIST_EVENTS,
                success=False,
                error_message=str(e)
            )
            raise CalendarError(f"Failed to list events: {str(e)}")
    
    def create_event(
        self,
        event_data: Dict[str, Any],
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new event in the specified calendar.
        
        Args:
            event_data: Event data including subject, start, end, etc.
            calendar_id: Calendar ID (default: "primary")
            user_input: Optional user input that triggered the creation
            
        Returns:
            Created event object
            
        Raises:
            CalendarError: If event creation fails
        """
        try:
            response = self._make_request(
                "POST",
                f"/me/calendars/{calendar_id}/events",
                data=event_data
            )
            
            self._log_action(
                action_type=CalendarActionType.CREATE_EVENT,
                success=True,
                user_input=user_input,
                event_id=response.get("id"),
                event_summary=response.get("subject"),
                event_start=datetime.fromisoformat(response["start"]["dateTime"].replace("Z", "+00:00")),
                event_end=datetime.fromisoformat(response["end"]["dateTime"].replace("Z", "+00:00")),
                provider_response=response
            )
            
            return response
        except Exception as e:
            self._log_action(
                action_type=CalendarActionType.CREATE_EVENT,
                success=False,
                user_input=user_input,
                error_message=str(e)
            )
            raise CalendarError(f"Failed to create event: {str(e)}")
    
    def update_event(
        self,
        event_id: str,
        event_data: Dict[str, Any],
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing event.
        
        Args:
            event_id: ID of the event to update
            event_data: Updated event data
            calendar_id: Calendar ID (default: "primary")
            user_input: Optional user input that triggered the update
            
        Returns:
            Updated event object
            
        Raises:
            CalendarError: If event update fails
        """
        try:
            response = self._make_request(
                "PATCH",
                f"/me/calendars/{calendar_id}/events/{event_id}",
                data=event_data
            )
            
            self._log_action(
                action_type=CalendarActionType.UPDATE_EVENT,
                success=True,
                user_input=user_input,
                event_id=event_id,
                event_summary=response.get("subject"),
                event_start=datetime.fromisoformat(response["start"]["dateTime"].replace("Z", "+00:00")),
                event_end=datetime.fromisoformat(response["end"]["dateTime"].replace("Z", "+00:00")),
                provider_response=response
            )
            
            return response
        except Exception as e:
            self._log_action(
                action_type=CalendarActionType.UPDATE_EVENT,
                success=False,
                user_input=user_input,
                event_id=event_id,
                error_message=str(e)
            )
            raise CalendarError(f"Failed to update event: {str(e)}")
    
    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> bool:
        """
        Delete an event.
        
        Args:
            event_id: ID of the event to delete
            calendar_id: Calendar ID (default: "primary")
            user_input: Optional user input that triggered the deletion
            
        Returns:
            True if deletion was successful
            
        Raises:
            CalendarError: If event deletion fails
        """
        try:
            self._make_request(
                "DELETE",
                f"/me/calendars/{calendar_id}/events/{event_id}"
            )
            
            self._log_action(
                action_type=CalendarActionType.DELETE_EVENT,
                success=True,
                user_input=user_input,
                event_id=event_id
            )
            
            return True
        except Exception as e:
            self._log_action(
                action_type=CalendarActionType.DELETE_EVENT,
                success=False,
                user_input=user_input,
                event_id=event_id,
                error_message=str(e)
            )
            raise CalendarError(f"Failed to delete event: {str(e)}")
    
    def get_free_slots(
        self,
        start_time: datetime,
        end_time: datetime,
        duration: timedelta,
        calendar_id: str = "primary",
    ) -> List[Dict[str, datetime]]:
        """
        Find free time slots in the specified time range.
        
        Args:
            start_time: Start of time range to search
            end_time: End of time range to search
            duration: Duration of required free slot
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            List of free time slots, each with start and end times
            
        Raises:
            CalendarError: If free slot search fails
        """
        try:
            # Get busy periods
            params = {
                "startDateTime": start_time.isoformat(),
                "endDateTime": end_time.isoformat(),
                "schedules": [self.user.email]
            }
            
            response = self._make_request(
                "POST",
                "/me/calendar/getSchedule",
                data=params
            )
            
            # Process busy periods to find free slots
            busy_periods = response.get("value", [{}])[0].get("scheduleItems", [])
            free_slots = []
            
            current_time = start_time
            for busy in busy_periods:
                busy_start = datetime.fromisoformat(busy["start"]["dateTime"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"]["dateTime"].replace("Z", "+00:00"))
                
                # Add free slot if there's enough time before busy period
                if busy_start - current_time >= duration:
                    free_slots.append({
                        "start": current_time,
                        "end": busy_start
                    })
                
                current_time = busy_end
            
            # Add final free slot if there's enough time
            if end_time - current_time >= duration:
                free_slots.append({
                    "start": current_time,
                    "end": end_time
                })
            
            return free_slots
        except Exception as e:
            raise CalendarError(f"Failed to find free slots: {str(e)}")


class MicrosoftCalendarClient:
    """
    Client for Microsoft Calendar operations.
    
    This class provides a higher-level interface for calendar operations,
    handling user lookup and service initialization.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Microsoft Calendar client.
        
        Args:
            db: Database session
        """
        self.db = db
        self._services: Dict[str, MicrosoftCalendarService] = {}
    
    def _init_service(self, user_id: str) -> MicrosoftCalendarService:
        """
        Initialize or retrieve a calendar service for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            MicrosoftCalendarService instance
            
        Raises:
            CalendarError: If user not found
        """
        if user_id not in self._services:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise CalendarError(f"User not found: {user_id}")
            self._services[user_id] = MicrosoftCalendarService(user, self.db)
        return self._services[user_id]
    
    def list_calendars(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all calendars for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of calendar objects
            
        Raises:
            CalendarError: If calendar listing fails
        """
        service = self._init_service(user_id)
        return service.list_calendars()
    
    def list_events(
        self,
        user_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        calendar_id: str = "primary",
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List events for a user.
        
        Args:
            user_id: User ID
            time_min: Start time for events
            time_max: End time for events
            calendar_id: Calendar ID (default: "primary")
            max_results: Maximum number of events to return
            
        Returns:
            List of event objects
            
        Raises:
            CalendarError: If event listing fails
        """
        service = self._init_service(user_id)
        return service.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results
        )
    
    def create_event(
        self,
        user_id: str,
        event_data: Dict[str, Any],
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an event for a user.
        
        Args:
            user_id: User ID
            event_data: Event data
            calendar_id: Calendar ID (default: "primary")
            user_input: Optional user input that triggered the creation
            
        Returns:
            Created event object
            
        Raises:
            CalendarError: If event creation fails
        """
        service = self._init_service(user_id)
        return service.create_event(
            event_data=event_data,
            calendar_id=calendar_id,
            user_input=user_input
        )
    
    def update_event(
        self,
        user_id: str,
        event_id: str,
        event_data: Dict[str, Any],
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an event for a user.
        
        Args:
            user_id: User ID
            event_id: Event ID
            event_data: Updated event data
            calendar_id: Calendar ID (default: "primary")
            user_input: Optional user input that triggered the update
            
        Returns:
            Updated event object
            
        Raises:
            CalendarError: If event update fails
        """
        service = self._init_service(user_id)
        return service.update_event(
            event_id=event_id,
            event_data=event_data,
            calendar_id=calendar_id,
            user_input=user_input
        )
    
    def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary",
        user_input: Optional[str] = None,
    ) -> bool:
        """
        Delete an event for a user.
        
        Args:
            user_id: User ID
            event_id: Event ID
            calendar_id: Calendar ID (default: "primary")
            user_input: Optional user input that triggered the deletion
            
        Returns:
            True if deletion was successful
            
        Raises:
            CalendarError: If event deletion fails
        """
        service = self._init_service(user_id)
        return service.delete_event(
            event_id=event_id,
            calendar_id=calendar_id,
            user_input=user_input
        )
    
    def get_free_slots(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        duration: timedelta,
        calendar_id: str = "primary",
    ) -> List[Dict[str, datetime]]:
        """
        Find free time slots for a user.
        
        Args:
            user_id: User ID
            start_time: Start of time range to search
            end_time: End of time range to search
            duration: Duration of required free slot
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            List of free time slots
            
        Raises:
            CalendarError: If free slot search fails
        """
        service = self._init_service(user_id)
        return service.get_free_slots(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            calendar_id=calendar_id
        )
