import pytest
from datetime import datetime, timedelta
from src.repositories.mongodb_repository import MongoDBRepository
from src.models.mongodb_models import User, Event, Session, AgentLog

@pytest.mark.asyncio
async def test_create_user(mongodb_repository, test_user):
    """Test user creation."""
    # User already created by fixture
    assert test_user.id is not None
    assert test_user.email == "test@example.com"

@pytest.mark.asyncio
async def test_get_user_by_email(mongodb_repository, test_user):
    """Test retrieving user by email."""
    repo = MongoDBRepository()
    user = await repo.get_user_by_email("test@example.com")
    assert user is not None
    assert user.email == test_user.email
    assert user.id == test_user.id

@pytest.mark.asyncio
async def test_update_user_tokens(mongodb_repository, test_user):
    """Test updating user tokens."""
    repo = MongoDBRepository()
    tokens = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    success = await repo.update_user_tokens(test_user.id, "google", tokens)
    assert success is True

    # Verify update
    user = await repo.get_user_by_email(test_user.email)
    assert user.google_token == tokens

@pytest.mark.asyncio
async def test_create_event(mongodb_repository, test_user):
    """Test event creation."""
    repo = MongoDBRepository()
    event = Event(
        user_id=test_user.id,
        provider="google",
        provider_event_id="test_event_2",
        summary="Test Event 2",
        start=datetime.utcnow(),
        end=datetime.utcnow() + timedelta(hours=1)
    )
    created_event = await repo.create_event(event)
    assert created_event.id is not None
    assert created_event.summary == "Test Event 2"

@pytest.mark.asyncio
async def test_get_user_events(mongodb_repository, test_user, test_event):
    """Test retrieving user events."""
    repo = MongoDBRepository()
    start = datetime.utcnow() - timedelta(days=1)
    end = datetime.utcnow() + timedelta(days=1)
    events = await repo.get_user_events(test_user.id, start, end)
    assert len(events) >= 1
    assert any(e.id == test_event.id for e in events)

@pytest.mark.asyncio
async def test_create_session(mongodb_repository, test_user):
    """Test session creation."""
    repo = MongoDBRepository()
    session = Session(
        user_id=test_user.id,
        provider="google",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    created_session = await repo.create_session(session)
    assert created_session.id is not None
    assert created_session.access_token == "test_access_token"

@pytest.mark.asyncio
async def test_get_active_session(mongodb_repository, test_user, test_session):
    """Test retrieving active session."""
    repo = MongoDBRepository()
    session = await repo.get_active_session(test_user.id, "google")
    assert session is not None
    assert session.id == test_session.id
    assert session.access_token == test_session.access_token

@pytest.mark.asyncio
async def test_create_agent_log(mongodb_repository, test_user):
    """Test agent log creation."""
    repo = MongoDBRepository()
    log = AgentLog(
        user_id=test_user.id,
        intent="test_intent",
        input_text="test input",
        steps=[{"step": 1, "action": "test_action"}],
        final_output="test output"
    )
    created_log = await repo.create_agent_log(log)
    assert created_log.id is not None
    assert created_log.intent == "test_intent"

@pytest.mark.asyncio
async def test_get_user_agent_logs(mongodb_repository, test_user, test_agent_log):
    """Test retrieving user agent logs."""
    repo = MongoDBRepository()
    logs = await repo.get_user_agent_logs(test_user.id)
    assert len(logs) >= 1
    assert any(log.id == test_agent_log.id for log in logs) 