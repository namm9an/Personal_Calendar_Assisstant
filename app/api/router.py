"""
Main API router for the Personal Calendar Assistant.
"""
from fastapi import APIRouter

from app.api.calendar import router as calendar_router
from app.api.ms_calendar import router as ms_calendar_router
from src.api.agent_calendar import router as agent_router


# Create the main API router
router = APIRouter()

# Include sub-routers
router.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])
router.include_router(ms_calendar_router, prefix="/ms/calendar", tags=["Microsoft Calendar"])
router.include_router(agent_router, prefix="/agent", tags=["Agent"])

# TODO: Add agent router once implemented
# router.include_router(agent_router, prefix="/agent", tags=["Agent"])
