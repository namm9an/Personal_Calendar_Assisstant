from typing import Dict, Any, Optional
from fastapi import HTTPException, status

class ServiceError(Exception):
    """Base exception for service errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(ServiceError):
    """Database operation error."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfigError(ServiceError):
    """Configuration error."""
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthError(ServiceError):
    """Authentication error."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class OAuthError(ServiceError):
    """OAuth error."""
    def __init__(self, message: str = "OAuth Error"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class CalendarServiceError(ServiceError):
    """Calendar service error."""
    def __init__(self, message: str = "Calendar service error"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)


class EncryptionError(ServiceError):
    """Encryption/decryption error."""
    def __init__(self, message: str = "Encryption or decryption failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


# For compatibility with src/core/exceptions.py
class BaseError(Exception):
    """Base exception class for the application."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ToolExecutionError(BaseError):
    """Raised when a tool execution fails."""
    def __init__(
        self,
        message: str = "Tool execution failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=500, details=details)

class CalendarError(Exception):
    """Custom exception for calendar-related errors."""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass
