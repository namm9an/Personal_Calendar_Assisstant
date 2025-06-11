# Personal Calendar Assistant

An AI-powered calendar management system that helps you manage your calendar events across Google Calendar and Microsoft Outlook using natural language instructions.

## Features

- Google Calendar integration
- Microsoft Outlook integration
- Natural language understanding
- Cross-calendar event management
- Secure token handling with encryption
- Multi-provider orchestration
- MongoDB storage for data persistence
- Docker deployment for production environments

## Project Phases

### Phase 1: Google Calendar Integration
- Set up basic project structure
- Implement Google OAuth2 authentication
- Create Google Calendar service
- Add calendar operation tools (list, create, update, delete events)

### Phase 2: Microsoft Calendar Integration & Encryption
- Implement Microsoft OAuth2 authentication
- Create Microsoft Calendar service
- Add secure token encryption for storage
- Add cross-provider calendar tools

### Phase 3: Agent & Multi-Provider Orchestration
- Add intent detection for natural language processing
- Implement LLM-based agent for calendar operations
- Create multi-provider orchestration layer
- Add more sophisticated calendar tools (find free slots, etc.)

### Phase 4: MongoDB Migration & Deployment
- Migrate data storage to MongoDB for scalability
- Create MongoDB models and repositories
- Update application to use MongoDB
- Add Docker setup for containerization

### Phase 5: Production Deployment
- Docker Compose configuration for multi-container deployment
- NGINX integration for reverse proxy and SSL termination
- Health check endpoint for monitoring
- Production deployment documentation
- Environment configuration for different deployment environments

## Getting Started

### Prerequisites

- Python 3.10+
- Google API credentials
- Microsoft API credentials
- MongoDB (local or Atlas)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-calendar-assistant.git
cd personal-calendar-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (create a .env file):
```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=calendar_db
ENCRYPTION_KEY=your_secure_encryption_key
```

4. Run the application:
```bash
uvicorn src.app:app --reload
```

## Deployment

For production deployment, we provide Docker and Docker Compose configuration files:

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

2. Or use the deployment script:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

See the [Deployment Guide](docs/deployment.md) for detailed instructions.

## API Documentation

When running the application, access the API documentation at:
- http://localhost:8000/api/docs

## Testing

Run tests with pytest:
```bash
pip install -r requirements-test.txt
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- FastAPI team for the excellent framework
- MongoDB team for the database
- Google and Microsoft for their calendar APIs
- The open-source community
