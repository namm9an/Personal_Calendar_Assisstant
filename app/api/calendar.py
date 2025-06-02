"""
Calendar API routes.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.postgres import get_db
from app.models.user import User
from app.schemas.calendar import (
    Event,
    EventCreate,
    EventUpdate,
    FreeSlotRequest,
    FreeSlotResponse,
)
from app.services.google_calendar import GoogleCalendarClient


router = APIRouter()


@router.get("/calendars", response_model=List[dict])
async def list_calendars(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all calendars for the current user.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        return calendar_client.list_calendars(str(user.id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list calendars: {str(e)}",
        )


@router.get("/events", response_model=List[Event])
async def list_events(
    from_date: datetime = Query(..., alias="from"),
    to_date: datetime = Query(..., alias="to"),
    calendar_id: Optional[str] = "primary",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List events for the current user within the specified date range.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        return calendar_client.list_events(
            user_id=str(user.id),
            time_min=from_date,
            time_max=to_date,
            calendar_id=calendar_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}",
        )


@router.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new event for the current user.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        return calendar_client.create_event(
            user_id=str(user.id),
            event_create=event,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )


@router.get("/events/{event_id}", response_model=Event)
async def get_event(
    event_id: str,
    calendar_id: Optional[str] = "primary",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific event by ID for the current user.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        # Since there's no direct get_event in the service, we'll use list_events
        # with a tight timeframe and filter for the specific event
        # In a real implementation, you'd have a get_event method in the service
        
        # This is a placeholder implementation
        # In practice, you would implement a get_event method in the calendar service
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Get event by ID not implemented yet",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event: {str(e)}",
        )


@router.patch("/events/{event_id}", response_model=Event)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    calendar_id: Optional[str] = "primary",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing event for the current user.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        return calendar_client.update_event(
            user_id=str(user.id),
            event_id=event_id,
            event_update=event_update,
            calendar_id=calendar_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}",
        )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    calendar_id: Optional[str] = "primary",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an event for the current user.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        calendar_client.delete_event(
            user_id=str(user.id),
            event_id=event_id,
            calendar_id=calendar_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}",
        )


@router.post("/free-slots", response_model=FreeSlotResponse)
async def find_free_slots(
    request: FreeSlotRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Find free time slots for the current user based on the request criteria.
    """
    calendar_client = GoogleCalendarClient(db)
    try:
        return calendar_client.find_free_slots(
            user_id=str(user.id),
            free_slot_request=request,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find free slots: {str(e)}",
        )
