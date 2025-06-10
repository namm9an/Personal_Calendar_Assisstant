"""Factory for creating calendar service instances."""
from typing import Optional
from src.services.calendar_service import CalendarService
from src.services.microsoft_calendar_service import MicrosoftCalendarService
from src.services.google_calendar_service import GoogleCalendarService
from src.core.exceptions import ToolExecutionError

async def get_calendar_service(provider: str, user_id: str) -> CalendarService:
    """Get the appropriate calendar service instance.
    
    Args:
        provider: The calendar provider ("microsoft" or "google")
        user_id: The user ID to get the service for
        
    Returns:
        An instance of the appropriate calendar service
        
    Raises:
        ToolExecutionError: If the provider is not supported
    """
    if provider == "microsoft":
        return MicrosoftCalendarService(user_id)
    elif provider == "google":
        return GoogleCalendarService(user_id)
    else:
        raise ToolExecutionError(f"Unsupported provider: {provider}") 