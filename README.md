# Personal Calendar Assistant

An AI-powered calendar management system that helps users manage their schedules across multiple calendar providers (Google Calendar and Microsoft Calendar).

## Features

- 🤖 AI-powered calendar management
- 📅 Multi-provider support (Google & Microsoft)
- 🔄 Real-time synchronization
- 🔒 Secure OAuth authentication
- 📱 Responsive web interface
- 📊 Analytics and insights
- 🔔 Smart notifications

## Tech Stack

- **Backend**: FastAPI, Python 3.10+
- **Database**: MongoDB Atlas
- **Cache**: Redis
- **AI/ML**: Google Gemini
- **Authentication**: OAuth 2.0
- **Deployment**: Docker, Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- MongoDB Atlas account
- Redis instance
- Google Cloud Platform account
- Microsoft Azure account
- Google Gemini API key

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/personal-calendar-assistant.git
   cd personal-calendar-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration values.

5. Start the development environment:
   ```bash
   docker-compose up --build
   ```

The application will be available at:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthz

## Project Structure

```
personal-calendar-assistant/
├── src/
│   ├── api/              # API routes
│   ├── core/             # Core functionality
│   ├── db/               # Database models and connection
│   ├── models/           # Pydantic models
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Request/response schemas
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── k8s/                  # Kubernetes manifests
├── monitoring/           # Monitoring configuration
├── .env.example          # Environment template
├── docker-compose.yml    # Docker Compose config
├── Dockerfile           # Docker configuration
└── README.md            # This file
```

## API Documentation

The API documentation is available at `/docs` when running the application. It provides detailed information about:

- Authentication endpoints
- Calendar management endpoints
- AI agent endpoints
- Webhook endpoints

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src
```

## Deployment

### Docker

Build the image:
```bash
docker build -t personal-calendar-assistant .
```

Run the container:
```bash
docker run -p 8000:8000 personal-calendar-assistant
```

### Kubernetes

Deploy to Kubernetes:
```bash
kubectl apply -f k8s/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- FastAPI team for the excellent framework
- MongoDB team for the database
- Google and Microsoft for their calendar APIs
- The open-source community
