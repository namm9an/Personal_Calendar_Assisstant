# Calendar Agent Documentation

## Overview

The Calendar Agent is a conversational interface for managing calendar events. It uses a two-tier LLM setup:
- **Primary**: Google's Gemini Pro for high-quality responses
- **Fallback**: Local Mistral-7B model for cost-effective operation

## Prompt Templates

The agent uses few-shot prompt templates for each intent. Templates are located in `src/agents/prompts/`:

### List Events Template
```txt
System: You are an AI scheduling assistant. You receive a user's natural language command and must return a JSON object matching the ListEventsInput schema for the requested tool.

Examples:
User: "What events do I have next Tuesday between 9 AM and 12 PM?"
Assistant: {
  "provider": "google",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "start": "2025-06-10T09:00:00Z",
  "end": "2025-06-10T12:00:00Z"
}
```

### Find Free Slots Template
```txt
System: You are an AI scheduling assistant. You receive a user's natural language command and must return a JSON object matching the FreeSlotsInput schema for the requested tool.

Examples:
User: "Find a 30-minute slot tomorrow afternoon"
Assistant: {
  "provider": "google",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "duration_minutes": 30,
  "range_start": "2025-06-02T12:00:00Z",
  "range_end": "2025-06-02T17:00:00Z"
}
```

### Create Event Template
```txt
System: You are an AI scheduling assistant. You receive a user's natural language command and must return a JSON object matching the CreateEventInput schema for the requested tool.

Examples:
User: "Schedule a team meeting tomorrow at 2 PM for 1 hour with alice@example.com"
Assistant: {
  "provider": "google",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "summary": "Team Meeting",
  "start": "2025-06-02T14:00:00Z",
  "end": "2025-06-02T15:00:00Z",
  "description": "Team meeting with Alice",
  "attendees": [
    {"email": "alice@example.com", "name": "Alice"}
  ]
}
```

### Reschedule Event Template
```txt
System: You are an AI scheduling assistant. You receive a user's natural language command and must return a JSON object matching the RescheduleEventInput schema for the requested tool.

Examples:
User: "Move my team meeting tomorrow to 3 PM"
Assistant: {
  "provider": "google",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "event_id": "team_meeting_123",
  "new_start": "2025-06-02T15:00:00Z",
  "new_end": "2025-06-02T16:00:00Z"
}
```

### Cancel Event Template
```txt
System: You are an AI scheduling assistant. You receive a user's natural language command and must return a JSON object matching the CancelEventInput schema for the requested tool.

Examples:
User: "Cancel my team meeting tomorrow"
Assistant: {
  "provider": "google",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "event_id": "team_meeting_123"
}
```

## API Usage

### Endpoint
```
POST /api/v1/agent/calendar
```

### Request Format
```json
{
  "text": "Show me my calendar for tomorrow",
  "provider": "google"
}
```

### Response Format (Server-Sent Events)
The endpoint streams Server-Sent Events (SSE) with the following format:

1. **Step Events**:
```json
{
  "step_number": 1,
  "message": "Analyzing your request...",
  "tool_invoked": null,
  "tool_input": null,
  "tool_output": null,
  "timestamp": "2025-06-01T12:00:00Z"
}
```

2. **Final Response**:
```json
{
  "final_intent": "list_events",
  "final_output": {
    "events": [...]
  },
  "summary": "Successfully processed list_events request",
  "steps": [...],
  "timestamp": "2025-06-01T12:00:05Z"
}
```

### Example Usage
```bash
# Using curl
curl -N -X POST http://localhost:8000/api/v1/agent/calendar \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule a meeting tomorrow at 2 PM with alice@example.com",
    "provider": "google"
  }'

# Using Python
import requests
import sseclient

response = requests.post(
    "http://localhost:8000/api/v1/agent/calendar",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "text": "Schedule a meeting tomorrow at 2 PM with alice@example.com",
        "provider": "google"
    },
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    print(event.data)
```

## Fallback Logic

The agent implements automatic fallback from Gemini Pro to the local Mistral-7B model in these cases:
1. User has exceeded their Gemini Pro quota
2. Gemini Pro API is unavailable or returns an error
3. `FORCE_LOCAL_LLM=true` environment variable is set

### Configuration
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
FORCE_LOCAL_LLM=true  # Force use of local model
```

## Error Handling

The agent handles various error scenarios:

1. **Unknown Intent**:
```json
{
  "error": "Could not recognize intent from input",
  "details": null,
  "timestamp": "2025-06-01T12:00:00Z"
}
```

2. **Tool Execution Error**:
```json
{
  "error": "Failed to execute calendar tool",
  "details": {
    "intent": "list_events",
    "tool": "calendar_tool"
  },
  "timestamp": "2025-06-01T12:00:00Z"
}
```

3. **LLM Error**:
```json
{
  "error": "Failed to generate response",
  "details": {
    "model": "gemini-pro",
    "fallback_attempted": true
  },
  "timestamp": "2025-06-01T12:00:00Z"
}
```

## Monitoring

The agent exposes Prometheus metrics:

- `agent_llm_fallback_count`: Number of times LLM fallback occurred
- `agent_llm_call_latency_seconds`: Time spent in LLM calls

Example query:
```promql
# Fallback rate by user
rate(agent_llm_fallback_count[5m])

# Average LLM latency by model
rate(agent_llm_call_latency_seconds_sum[5m]) / rate(agent_llm_call_latency_seconds_count[5m])
``` 