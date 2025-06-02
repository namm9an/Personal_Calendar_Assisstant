# Database Documentation

## MongoDB Integration

The Personal Calendar Assistant uses MongoDB as its primary database, providing a flexible and scalable storage solution for user data, calendar events, sessions, and agent logs.

### Connection Configuration

The MongoDB connection is configured through environment variables:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=calendar_assistant
```

### Data Models

#### User
- `email`: User's email address (unique)
- `google_token`: Google OAuth tokens
- `microsoft_token`: Microsoft OAuth tokens

#### Event
- `user_id`: Reference to user
- `provider`: Calendar provider (google/microsoft)
- `provider_event_id`: Event ID from provider
- `summary`: Event title
- `start`: Event start time
- `end`: Event end time
- `description`: Event description
- `location`: Event location
- `attendees`: List of attendee emails

#### Session
- `user_id`: Reference to user
- `provider`: Calendar provider
- `access_token`: OAuth access token
- `refresh_token`: OAuth refresh token
- `expires_at`: Token expiration time

#### AgentLog
- `user_id`: Reference to user
- `intent`: Detected user intent
- `input_text`: Original user input
- `steps`: List of processing steps
- `final_output`: Agent's response

### Indexes

The following indexes are created for optimal query performance:

```python
# Users collection
db.users.create_index("email", unique=True)

# Events collection
db.events.create_index([
    ("user_id", 1),
    ("start", 1),
    ("end", 1)
])

# Sessions collection
db.sessions.create_index([
    ("user_id", 1),
    ("provider", 1),
    ("expires_at", 1)
])

# Agent logs collection
db.agent_logs.create_index([
    ("user_id", 1),
    ("created_at", -1)
])
```

### Repository Layer

The `MongoDBRepository` class provides a clean interface for database operations:

```python
class MongoDBRepository:
    async def get_user_by_email(self, email: str) -> Optional[User]
    async def update_user_tokens(self, user_id: str, provider: str, tokens: dict) -> bool
    async def create_event(self, event: Event) -> Event
    async def get_user_events(self, user_id: str, start: datetime, end: datetime) -> List[Event]
    async def create_session(self, session: Session) -> Session
    async def get_active_session(self, user_id: str, provider: str) -> Optional[Session]
    async def create_agent_log(self, log: AgentLog) -> AgentLog
    async def get_user_agent_logs(self, user_id: str) -> List[AgentLog]
```

### Development Setup

1. Start MongoDB using Docker Compose:
```bash
docker-compose up -d mongodb
```

2. Initialize the database with sample data:
```bash
python scripts/init_mongodb.py
```

### Testing

The test suite includes comprehensive tests for all database operations:

```bash
pytest tests/test_mongodb.py
```

The tests use a separate test database and clean up after themselves.

### Monitoring

MongoDB metrics are exposed through Prometheus:

- Connection pool size
- Operation latency
- Query performance
- Index usage
- Memory usage

### Backup and Recovery

Regular backups are recommended. Use MongoDB's built-in tools:

```bash
# Create backup
mongodump --uri="mongodb://localhost:27017" --db=calendar_assistant --out=/backup

# Restore from backup
mongorestore --uri="mongodb://localhost:27017" --db=calendar_assistant /backup/calendar_assistant
```

### Security Considerations

1. Use environment variables for sensitive configuration
2. Implement proper access control
3. Enable authentication in production
4. Use SSL/TLS for connections
5. Regular security audits
6. Data encryption at rest

### Performance Optimization

1. Use appropriate indexes
2. Monitor query performance
3. Implement connection pooling
4. Use proper data types
5. Regular maintenance tasks
6. Monitor resource usage 