import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.agent_calendar import detect_intent, load_prompt_template
from src.schemas.agent_schemas import AgentRequest, AgentResponse, AgentStep, AgentError
from app.main import app
from app.config import settings
from app.core.exceptions import ToolExecutionError
from app.models.types import UniversalUUID
from app.models.mongodb_models import User, Event, Session
from datetime import datetime, timedelta
import json
import inspect

@pytest.fixture
def client():
    """Get a TestClient instance for the app."""
    return TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        email="test@example.com",
        name="Test User",
        id=str(UniversalUUID()),
        google_access_token="google_test_token",
        google_refresh_token="google_refresh_token",
        microsoft_access_token="ms_test_token",
        microsoft_refresh_token="ms_refresh_token"
    )

@pytest.fixture
def test_session(test_user):
    """Create a test session."""
    return {
        "user_id": "test_user_id",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }

# Helper for detect_intent tests
async def detect_intent_helper(text: str) -> dict:
    """Helper function to test detect_intent with text.
    This calls the non-endpoint detect_intent function with the text.
    """
    # Call the original detect_intent function directly from src.api.agent_calendar
    from src.api.agent_calendar import detect_intent as detect_intent_function
    intent = detect_intent_function(text)
    return {"intent": intent, "confidence": 0.9}

@pytest.mark.asyncio
async def test_detect_intent():
    """Test intent detection from user text."""
    # Test list events intent
    result = await detect_intent_helper("Show me my calendar for tomorrow")
    assert result["intent"] == "list_events"
    result = await detect_intent_helper("What events do I have today?")
    assert result["intent"] == "list_events"
    
    # Test find free slots intent
    result = await detect_intent_helper("Find a free slot tomorrow afternoon")
    assert result["intent"] == "find_free_slots"
    result = await detect_intent_helper("When am I available for a meeting?")
    assert result["intent"] == "find_free_slots"
    
    # Test create event intent
    result = await detect_intent_helper("Schedule a meeting with John tomorrow")
    assert result["intent"] == "create_event"
    result = await detect_intent_helper("Book a team meeting for Friday")
    assert result["intent"] == "create_event"
    
    # Test reschedule event intent
    result = await detect_intent_helper("Move my meeting to 3 PM")
    assert result["intent"] == "reschedule_event"
    result = await detect_intent_helper("Change the team meeting time")
    assert result["intent"] == "reschedule_event"
    
    # Test cancel event intent
    result = await detect_intent_helper("Cancel my meeting tomorrow")
    assert result["intent"] == "cancel_event"
    result = await detect_intent_helper("Delete the team meeting")
    assert result["intent"] == "cancel_event"
    
    # Test unknown intent
    result = await detect_intent_helper("Hello, how are you?")
    assert result["intent"] == "unknown"

@pytest.mark.asyncio
async def test_load_prompt_template():
    """Test loading and formatting prompt templates."""
    # Test loading list events template
    # Check if load_prompt_template is a regular function or a coroutine
    prompt_func = load_prompt_template
    prompt = None
    
    if inspect.iscoroutinefunction(prompt_func):
        # It's a coroutine, await it
        prompt = await prompt_func("list_events")
    else:
        # It's a regular function
        prompt = prompt_func("list_events")
        
    assert "System: You are an AI scheduling assistant" in prompt
    
    # Use the same approach for other templates
    if inspect.iscoroutinefunction(prompt_func):
        prompt = await prompt_func("find_free_slots")
    else:
        prompt = prompt_func("find_free_slots")
    assert "System: You are an AI scheduling assistant" in prompt
    
    if inspect.iscoroutinefunction(prompt_func):
        prompt = await prompt_func("create_event")
    else:
        prompt = prompt_func("create_event")
    assert "System: You are an AI scheduling assistant" in prompt
    
    if inspect.iscoroutinefunction(prompt_func):
        prompt = await prompt_func("reschedule_event")
    else:
        prompt = prompt_func("reschedule_event")
    assert "System: You are an AI scheduling assistant" in prompt
    
    if inspect.iscoroutinefunction(prompt_func):
        prompt = await prompt_func("cancel_event")
    else:
        prompt = prompt_func("cancel_event")
    assert "System: You are an AI scheduling assistant" in prompt
    
    # Test loading non-existent template - should not raise an error in this implementation
    if inspect.iscoroutinefunction(prompt_func):
        prompt = await prompt_func("unknown")
    else:
        prompt = prompt_func("unknown")
    assert "System: You are an AI scheduling assistant" in prompt

@patch('src.agents.llm_selector.user_quota_remaining', return_value=5)
@patch('src.agents.llms.gemini.GeminiProClient')
async def test_select_llm_model_quota_available(mock_gemini_client, mock_quota, test_user):
    """Test that GeminiProClient is selected when user quota is available."""
    from src.agents.llm_selector import select_llm_model
    await select_llm_model(test_user.id)
    mock_gemini_client.assert_called_once()

@patch('src.agents.llm_selector.user_quota_remaining', return_value=0)
@patch('src.agents.llms.llama2.LocalLlama2Client')
async def test_select_llm_model_quota_exhausted(mock_llama_client, mock_quota, test_user):
    """Test that LocalLlama2Client is selected when user quota is exhausted."""
    from src.agents.llm_selector import select_llm_model
    await select_llm_model(test_user.id)
    mock_llama_client.assert_called_once()

@pytest.mark.asyncio
async def test_run_calendar_agent_success(client, mock_llm_selector, mock_langgraph_runner):
    """Test successful calendar agent execution."""
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_langgraph_runner.run_stream):
        
        response = client.post(
            "/agent/calendar",
            json={
                "text": "Show me my calendar for tomorrow",
                "provider": "google"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # Parse SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:]  # Remove "data: " prefix
                events.append(event_data)
        
        # Should have 3 steps + final response
        assert len(events) == 4
        
        # First event should be a step
        step = AgentStep.parse_raw(events[0])
        assert step.step_number == 1
        assert "Analyzing" in step.message
        
        # Last event should be the final response
        final_response = AgentResponse.parse_raw(events[-1])
        assert final_response.final_intent == "list_events"
        assert final_response.summary.startswith("Successfully processed")

@pytest.mark.asyncio
async def test_run_calendar_agent_unknown_intent(client):
    """Test calendar agent with unknown intent."""
    response = client.post(
        "/agent/calendar",
        json={
            "text": "Hello, how are you?",
            "provider": "google"
        }
    )
    
    assert response.status_code == 400
    error = AgentError.parse_raw(response.json())
    assert "Could not recognize intent" in error.error

@pytest.mark.asyncio
async def test_run_calendar_agent_llm_fallback(client, mock_llm_selector, mock_langgraph_runner):
    """Test calendar agent with LLM fallback."""
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_langgraph_runner.run_stream):
        
        response = client.post(
            "/agent/calendar",
            json={
                "text": "Show me my calendar for tomorrow",
                "provider": "google"
            }
        )
        
        assert response.status_code == 200
        
        # Parse SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:]
                events.append(event_data)
        
        # Should still complete successfully despite fallback
        final_response = AgentResponse.parse_raw(events[-1])
        assert final_response.final_intent == "list_events"
        assert final_response.summary.startswith("Successfully processed")

@pytest.mark.asyncio
async def test_run_calendar_agent_tool_error(client, mock_llm_selector):
    """Test calendar agent with tool execution error."""
    # Mock LangGraph to raise an error
    async def mock_run_stream(*args, **kwargs):
        yield {
            "message": "Analyzing request...",
            "tool": None,
            "input": None,
            "output": None
        }
        raise Exception("Tool execution failed")
    
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_run_stream):
        
        response = client.post(
            "/agent/calendar",
            json={
                "text": "Show me my calendar for tomorrow",
                "provider": "google"
            }
        )
        
        assert response.status_code == 200
        
        # Parse SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:]
                events.append(event_data)
        
        # Should have error in final response
        final_response = AgentResponse.parse_raw(events[-1])
        assert "Error" in final_response.summary 

def test_agent_health_check(client):
    """Test agent health check endpoint."""
    response = client.get("/agent/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_intent_detection(client):
    """Test intent detection for various user inputs."""
    test_cases = [
        {
            "input": "Schedule a meeting with John tomorrow at 2pm",
            "expected_intent": "create_event",
            "expected_entities": {
                "participant": "John",
                "time": "tomorrow at 2pm"
            }
        }
    ]
    
    response = client.post(
        "/agent/detect_intent",
        json={"text": test_cases[0]["input"]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["intent"] == test_cases[0]["expected_intent"]

def test_agent_response_creation(client):
    """Test agent response creation."""
    response = client.post(
        "/agent/run",
        json={
            "text": "Schedule a meeting with John tomorrow at 2pm",
            "provider": "google"
        }
    )
    assert response.status_code == 200

def test_agent_error_handling(client):
    """Test agent error handling."""
    response = client.post(
        "/agent/run",
        json={
            "text": "Do something impossible",
            "provider": "invalid"
        }
    )
    assert response.status_code == 400

def test_agent_context_management(client):
    """Test agent context management."""
    response1 = client.post(
        "/agent/run",
        json={
            "text": "Schedule a meeting with John tomorrow",
            "provider": "google"
        }
    )
    assert response1.status_code == 200
    
    # Test context retrieval
    response2 = client.get("/agent/context")
    assert response2.status_code == 200
    context = response2.json()
    assert "context" in context
    assert "last_intent" in context["context"]

def test_agent_prompt_templates(client):
    """Test agent prompt template retrieval."""
    response = client.get(
        "/agent/prompt-templates"
    )
    assert response.status_code == 200
    templates = response.json()
    assert "templates" in templates

def test_agent_logging(client):
    """Test agent action logging."""
    response = client.post(
        "/agent/log",
        json={
            "action": "create_event",
            "success": True,
            "details": {
                "event_id": "123",
                "summary": "Test Event"
            }
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "logged"

def test_agent_rate_limiting(client):
    """Test agent rate limiting."""
    response = client.post(
        "/agent/detect_intent",
        json={"text": "Schedule a meeting"}
    )
    assert response.status_code == 200
    
    # Get rate limit status
    response = client.get("/agent/rate-limit")
    assert response.status_code == 200
    limits = response.json()
    assert "limit" in limits
    assert "remaining" in limits 