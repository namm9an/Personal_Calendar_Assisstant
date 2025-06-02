# Development Guide

This guide provides detailed information for developers working on the Personal Calendar Assistant project.

## Project Structure

```
personal-calendar-assistant/
├── src/
│   ├── agents/
│   │   ├── prompts/          # LLM prompt templates
│   │   ├── llms/            # LLM client implementations
│   │   └── llm_selector.py  # LLM selection and fallback logic
│   ├── api/
│   │   └── agent_calendar.py # FastAPI endpoints
│   ├── calendar/
│   │   ├── google.py        # Google Calendar wrapper
│   │   └── microsoft.py     # Microsoft Calendar wrapper
│   ├── schemas/
│   │   └── agent_schemas.py # Pydantic models
│   └── main.py              # Application entry point
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_agent_endpoint.py
│   └── test_calendar_tool_wrappers.py
├── docs/
│   ├── agent.md             # Agent documentation
│   ├── api.md               # API documentation
│   └── development.md       # This file
└── docker-compose.yml       # Docker configuration
```

## Development Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Google Cloud Platform account
- Microsoft Azure account

### Environment Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Required
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
GEMINI_API_KEY=your_api_key

# Optional
FORCE_LOCAL_LLM=true  # Force use of local model
```

### OAuth Setup

#### Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" and select "OAuth client ID"
5. Configure the OAuth consent screen
6. For "Application type", select "Web application"
7. Add authorized redirect URIs:
   - For local development: `http://localhost:8000/auth/google/callback`
   - For production: `https://your-domain.com/auth/google/callback`
8. Create the client and note the Client ID and Client Secret

#### Microsoft OAuth Setup

1. Go to the [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Enter a name for your application
5. For "Supported account types", select "Accounts in any organizational directory and personal Microsoft accounts"
6. Add redirect URIs:
   - For local development: `http://localhost:8000/auth/ms/callback`
   - For production: `https://your-domain.com/auth/ms/callback`
7. Click "Register"
8. Note the "Application (client) ID" and "Directory (tenant) ID"
9. Create a new client secret
10. Add the following permissions:
    - Microsoft Graph > Delegated permissions:
      - Calendars.Read
      - Calendars.ReadWrite
      - User.Read

## Development Workflow

### Running the Application

Start the development server:
```bash
uvicorn src.main:app --reload
```

Or using Docker:
```bash
docker-compose up
```

### Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_agent_endpoint.py
```

Run with coverage:
```bash
pytest --cov=src tests/
```

### Code Style

Format code:
```bash
black src/ tests/
isort src/ tests/
```

Check code style:
```bash
flake8 src/ tests/
```

### Adding New Features

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Implement your changes following the project structure

3. Add tests for your changes:
```bash
pytest tests/test_your_feature.py
```

4. Format and check your code:
```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

5. Create a pull request

## Architecture

### Calendar Tool Wrappers

The calendar tool wrappers (`src/calendar/google.py` and `src/calendar/microsoft.py`) handle interactions with the respective calendar APIs. They implement a common interface for:

- Listing events
- Finding free slots
- Creating events
- Rescheduling events
- Canceling events

### LLM Integration

The LLM integration consists of:

1. **LLM Clients** (`src/agents/llms/`):
   - `gemini.py`: Google's Gemini Pro client
   - `llama2.py`: Local Mistral-7B client

2. **LLM Selector** (`src/agents/llm_selector.py`):
   - Manages LLM selection based on quota and availability
   - Implements fallback logic
   - Tracks metrics for monitoring

3. **Prompt Templates** (`src/agents/prompts/`):
   - Few-shot examples for each intent
   - System instructions
   - Error handling patterns

### FastAPI Backend

The FastAPI backend (`src/api/agent_calendar.py`) provides:

1. **Calendar Agent Endpoint**:
   - POST `/api/v1/agent/calendar`
   - Server-Sent Events (SSE) for real-time updates
   - Error handling and validation

2. **Authentication**:
   - OAuth2 with Google and Microsoft
   - Token encryption for security

### Monitoring

The application exposes Prometheus metrics:

- `agent_llm_fallback_count`: Number of times LLM fallback occurred
- `agent_llm_call_latency_seconds`: Time spent in LLM calls

## Best Practices

1. **Error Handling**:
   - Use custom exception classes
   - Implement proper error messages
   - Log errors with context

2. **Testing**:
   - Write unit tests for all new features
   - Use fixtures for common setup
   - Mock external dependencies

3. **Code Style**:
   - Follow PEP 8 guidelines
   - Use type hints
   - Document public APIs

4. **Security**:
   - Never commit secrets
   - Validate all inputs
   - Use proper authentication

5. **Performance**:
   - Cache when appropriate
   - Use async/await for I/O
   - Monitor resource usage

## Troubleshooting

### Common Issues

1. **OAuth Errors**:
   - Check redirect URIs
   - Verify client credentials
   - Check token expiration

2. **LLM Issues**:
   - Check API key
   - Verify quota limits
   - Check model availability

3. **Calendar API Issues**:
   - Check permissions
   - Verify event format
   - Check rate limits

### Debugging

1. Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

2. Check logs:
```bash
docker-compose logs -f
```

3. Use the debugger:
```python
import pdb; pdb.set_trace()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Format and check your code
6. Create a pull request

## License

MIT License - see LICENSE file for details 