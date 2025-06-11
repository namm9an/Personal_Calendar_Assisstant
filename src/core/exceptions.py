from typing import Any, Dict, Optional

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

class DatabaseError(BaseError):
    """Raised when a database operation fails."""
    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=503, details=details)

class ValidationError(BaseError):
    """Raised when input validation fails."""
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=400, details=details)

class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=401, details=details)

class AuthorizationError(BaseError):
    """Raised when authorization fails."""
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=403, details=details)

class NotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=404, details=details)

class RateLimitError(BaseError):
    """Raised when rate limit is exceeded."""
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=429, details=details)

class ExternalServiceError(BaseError):
    """Raised when an external service call fails."""
    def __init__(
        self,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=502, details=details)

class ConfigurationError(BaseError):
    """Raised when there's a configuration error."""
    def __init__(
        self,
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=500, details=details)

class ToolExecutionError(BaseError):
    """Raised when a tool execution fails."""
    def __init__(
        self,
        message: str = "Tool execution failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=500, details=details)

class EncryptionError(BaseError):
    """Raised when encryption or decryption fails."""
    def __init__(
        self,
        message: str = "Encryption/decryption operation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=500, details=details) 