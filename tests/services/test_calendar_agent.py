import pytest
from datetime import datetime, timedelta
from src.services.calendar_agent import run_calendar_agent
from src.core.exceptions import ToolExecutionError

@pytest.mark.asyncio
async def test_list_events():
    """Test listing events."""
    result = await run_calendar_agent(
        text="list my events",
        user_id="test_user",
        provider="google"
    )
    assert "events" in result
    assert isinstance(result["events"], list)

@pytest.mark.asyncio
async def test_find_free_slots():
    """Test finding free slots."""
    result = await run_calendar_agent(
        text="find free slots for tomorrow",
        user_id="test_user",
        provider="google"
    )
    assert "slots" in result
    assert isinstance(result["slots"], list)

@pytest.mark.asyncio
async def test_create_event():
    """Test creating an event."""
    result = await run_calendar_agent(
        text="create a meeting tomorrow at 2pm",
        user_id="test_user",
        provider="google"
    )
    assert "event" in result
    assert isinstance(result["event"], dict)

@pytest.mark.asyncio
async def test_update_event():
    """Test updating an event."""
    result = await run_calendar_agent(
        text="update my meeting tomorrow to 3pm",
        user_id="test_user",
        provider="google"
    )
    assert "event" in result
    assert isinstance(result["event"], dict)

@pytest.mark.asyncio
async def test_delete_event():
    """Test deleting an event."""
    result = await run_calendar_agent(
        text="delete my meeting tomorrow",
        user_id="test_user",
        provider="google"
    )
    assert "success" in result
    assert isinstance(result["success"], bool)

@pytest.mark.asyncio
async def test_reschedule_event():
    """Test rescheduling an event."""
    result = await run_calendar_agent(
        text="reschedule my meeting to next week",
        user_id="test_user",
        provider="google"
    )
    assert "event" in result
    assert isinstance(result["event"], dict)

@pytest.mark.asyncio
async def test_cancel_event():
    """Test canceling an event."""
    result = await run_calendar_agent(
        text="cancel my meeting tomorrow",
        user_id="test_user",
        provider="google"
    )
    assert "success" in result
    assert isinstance(result["success"], bool)

@pytest.mark.asyncio
async def test_invalid_provider():
    """Test with invalid provider."""
    with pytest.raises(ToolExecutionError):
        await run_calendar_agent(
            text="list my events",
            user_id="test_user",
            provider="invalid"
        )

@pytest.mark.asyncio
async def test_invalid_action():
    """Test with invalid action."""
    with pytest.raises(ToolExecutionError):
        await run_calendar_agent(
            text="invalid action",
            user_id="test_user",
            provider="google"
        ) 