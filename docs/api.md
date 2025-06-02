# API Documentation

This document provides detailed information about the Personal Calendar Assistant API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints require authentication using OAuth2 with either Google or Microsoft. The authentication flow is as follows:

1. Redirect user to the authorization URL:
```
GET /auth/{provider}/login
```

Where `{provider}` is either `google` or `microsoft`.

2. User is redirected to the provider's login page
3. After successful login, the provider redirects back to:
```
GET /auth/{provider}/callback
```

4. The callback endpoint returns a JWT token that should be included in subsequent requests:
```
Authorization: Bearer <token>
```

## Calendar Agent Endpoint

### Process Calendar Command

Process a natural language command for calendar operations.

```
POST /api/v1/agent/calendar
```

#### Request

```json
{
  "text": "Schedule a meeting tomorrow at 2 PM with alice@example.com",
  "provider": "google"
}
```

| Field | Type | Description |
|-------|------|-------------|
| text | string | The natural language command |
| provider | string | The calendar provider ("google" or "microsoft") |

#### Response

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
  "final_intent": "create_event",
  "final_output": {
    "event": {
      "id": "event_123",
      "summary": "Meeting with Alice",
      "start": "2025-06-02T14:00:00Z",
      "end": "2025-06-02T15:00:00Z",
      "attendees": [
        {
          "email": "alice@example.com",
          "name": "Alice"
        }
      ]
    }
  },
  "summary": "Successfully scheduled meeting with Alice",
  "steps": [
    {
      "step_number": 1,
      "message": "Analyzing your request...",
      "tool_invoked": null,
      "tool_input": null,
      "tool_output": null,
      "timestamp": "2025-06-01T12:00:00Z"
    },
    {
      "step_number": 2,
      "message": "Creating calendar event...",
      "tool_invoked": "calendar_tool",
      "tool_input": {
        "provider": "google",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "summary": "Meeting with Alice",
        "start": "2025-06-02T14:00:00Z",
        "end": "2025-06-02T15:00:00Z",
        "attendees": [
          {
            "email": "alice@example.com",
            "name": "Alice"
          }
        ]
      },
      "tool_output": {
        "event_id": "event_123"
      },
      "timestamp": "2025-06-01T12:00:02Z"
    }
  ],
  "timestamp": "2025-06-01T12:00:05Z"
}
```

#### Error Responses

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
    "intent": "create_event",
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

#### Example Usage

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

## Supported Commands

The calendar agent supports the following types of commands:

### List Events

Examples:
- "Show me my calendar for tomorrow"
- "What events do I have next Tuesday between 9 AM and 12 PM?"
- "List my meetings for this week"

### Find Free Slots

Examples:
- "Find a 30-minute slot tomorrow afternoon"
- "When am I free next week?"
- "Find a 1-hour slot for a team meeting"

### Create Event

Examples:
- "Schedule a team meeting tomorrow at 2 PM for 1 hour with alice@example.com"
- "Create a lunch meeting with John on Friday at noon"
- "Set up a call with the marketing team next Monday at 10 AM"

### Reschedule Event

Examples:
- "Move my team meeting tomorrow to 3 PM"
- "Reschedule my lunch with John to 1 PM"
- "Change the marketing call to Tuesday at 2 PM"

### Cancel Event

Examples:
- "Cancel my team meeting tomorrow"
- "Delete my lunch with John"
- "Remove the marketing call from my calendar"

## Rate Limits

The API implements the following rate limits:

- 100 requests per minute per user
- 1000 requests per hour per user
- 10000 requests per day per user

Rate limit headers are included in the response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1622548800
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - LLM service unavailable |

## Monitoring

The API exposes Prometheus metrics at `/metrics`:

- `agent_llm_fallback_count`: Number of times LLM fallback occurred
- `agent_llm_call_latency_seconds`: Time spent in LLM calls
- `agent_request_count`: Number of requests processed
- `agent_request_latency_seconds`: Time spent processing requests
- `agent_error_count`: Number of errors encountered

Example queries:
```promql
# Request rate by endpoint
rate(agent_request_count[5m])

# Error rate by type
rate(agent_error_count[5m])

# Average request latency
rate(agent_request_latency_seconds_sum[5m]) / rate(agent_request_latency_seconds_count[5m])
```

## Versioning

The API is versioned in the URL path:

```
/api/v1/agent/calendar
```

Breaking changes will be released in new versions (v2, v3, etc.).

## Support

For support, please:

1. Check the [documentation](docs/)
2. Open an issue on GitHub
3. Contact the development team

## License

MIT License - see LICENSE file for details 