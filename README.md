# Personal Calendar Assistant

[![Build Status](https://img.shields.io/github/actions/workflow/status/username/personal-calendar-assistant/ci.yml?branch=main&style=flat-square)](https://github.com/username/personal-calendar-assistant/actions)
[![Code Coverage](https://img.shields.io/codecov/c/github/username/personal-calendar-assistant?style=flat-square)](https://codecov.io/gh/username/personal-calendar-assistant)
[![License](https://img.shields.io/github/license/username/personal-calendar-assistant?style=flat-square)](LICENSE)

A smart calendar assistant that helps you manage your schedule using natural language commands. The assistant supports both Google Calendar and Microsoft Calendar, with a conversational interface powered by LLMs.

## Features

- **Natural Language Interface**: Talk to your calendar in plain English
- **Multi-Provider Support**: Works with both Google Calendar and Microsoft Calendar
- **Smart Scheduling**: Find free slots, schedule meetings, and manage events
- **Fallback Support**: Uses local LLM when cloud LLM is unavailable
- **Real-time Updates**: Server-Sent Events for live progress updates

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-calendar-assistant.git
cd personal-calendar-assistant
```

2. Set up environment variables:
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

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the server:
```bash
uvicorn src.main:app --reload
```

5. Access the API at `http://localhost:8000`

## API Usage

### Calendar Agent Endpoint

```bash
curl -N -X POST http://localhost:8000/api/v1/agent/calendar \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule a meeting tomorrow at 2 PM with alice@example.com",
    "provider": "google"
  }'
```

The endpoint streams Server-Sent Events (SSE) with real-time updates about the agent's progress.

### Example Commands

- "Show me my calendar for tomorrow"
- "Find a 30-minute slot tomorrow afternoon"
- "Schedule a team meeting tomorrow at 2 PM for 1 hour with alice@example.com"
- "Move my team meeting tomorrow to 3 PM"
- "Cancel my team meeting tomorrow"

## Architecture

The system consists of several key components:

1. **Calendar Tool Wrappers**: Handle interactions with Google and Microsoft Calendar APIs
2. **LLM Integration**: Uses Gemini Pro with local Mistral-7B fallback
3. **FastAPI Backend**: Provides RESTful API endpoints
4. **Prompt Templates**: Few-shot examples for each intent
5. **Monitoring**: Prometheus metrics for observability

## Documentation

- [Calendar Agent](docs/agent.md): Detailed documentation of the calendar agent
- [API Reference](docs/api.md): API endpoint documentation
- [Development Guide](docs/development.md): Guide for developers

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

### Docker Support

```bash
docker-compose up
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
