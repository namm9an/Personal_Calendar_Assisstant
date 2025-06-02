import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.agent_calendar import detect_intent, load_prompt_template
from src.schemas.agent_schemas import AgentRequest, AgentResponse, AgentStep, AgentError

def test_detect_intent():
    """Test intent detection from user text."""
    # Test list events intent
    assert detect_intent("Show me my calendar for tomorrow") == "list_events"
    assert detect_intent("What events do I have today?") == "list_events"
    
    # Test find free slots intent
    assert detect_intent("Find a free slot tomorrow afternoon") == "find_free_slots"
    assert detect_intent("When am I available for a meeting?") == "find_free_slots"
    
    # Test create event intent
    assert detect_intent("Schedule a meeting with John tomorrow") == "create_event"
    assert detect_intent("Book a team meeting for Friday") == "create_event"
    
    # Test reschedule event intent
    assert detect_intent("Move my meeting to 3 PM") == "reschedule_event"
    assert detect_intent("Change the team meeting time") == "reschedule_event"
    
    # Test cancel event intent
    assert detect_intent("Cancel my meeting tomorrow") == "cancel_event"
    assert detect_intent("Delete the team meeting") == "cancel_event"
    
    # Test unknown intent
    assert detect_intent("Hello, how are you?") == "unknown"

def test_load_prompt_template():
    """Test loading and formatting prompt templates."""
    # Test loading list events template
    prompt = load_prompt_template("list_events", "Show me my calendar")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Show me my calendar" in prompt
    
    # Test loading find free slots template
    prompt = load_prompt_template("find_free_slots", "Find a free slot")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Find a free slot" in prompt
    
    # Test loading create event template
    prompt = load_prompt_template("create_event", "Schedule a meeting")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Schedule a meeting" in prompt
    
    # Test loading reschedule event template
    prompt = load_prompt_template("reschedule_event", "Move my meeting")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Move my meeting" in prompt
    
    # Test loading cancel event template
    prompt = load_prompt_template("cancel_event", "Cancel my meeting")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Cancel my meeting" in prompt
    
    # Test loading non-existent template
    with pytest.raises(Exception):
        load_prompt_template("unknown", "Some text")

@pytest.mark.asyncio
async def test_run_calendar_agent_success(client, mock_llm_selector, mock_langgraph_runner):
    """Test successful calendar agent execution."""
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_langgraph_runner.run_stream):
        
        response = client.post(
            "/api/v1/agent/calendar",
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
        "/api/v1/agent/calendar",
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
            "/api/v1/agent/calendar",
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
            "/api/v1/agent/calendar",
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