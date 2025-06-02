import uuid
from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

class UniversalUUID(TypeDecorator):
    """UUID type that works across PostgreSQL and SQLite
    
    This type will use PostgreSQL's native UUID type when connected to PostgreSQL,
    and will use String(36) for SQLite and other databases. It handles proper
    conversion between UUID objects and string representations in both directions.
    """
    
    impl = String(36)  # Base implementation for SQLite
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif isinstance(value, uuid.UUID):
            return str(value)
        elif isinstance(value, str):
            try:
                # Validate it's a proper UUID
                uuid.UUID(value)
                return value
            except ValueError:
                raise ValueError(f"Invalid UUID format: {value}")
        else:
            raise TypeError(f"Expected UUID or string, got {type(value)}")
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)
