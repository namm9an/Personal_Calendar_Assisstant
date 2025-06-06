class ToolExecutionError(Exception):
    """Custom exception for errors that occur during tool execution."""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message

    def __str__(self):
        if self.original_exception:
            return f"{self.message} (Original error: {type(self.original_exception).__name__}: {str(self.original_exception)})"
        return self.message

class CalendarError(Exception):
    """Custom exception for calendar-related errors."""
    pass

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class EncryptionError(Exception):
    """Custom exception for encryption errors."""
    pass

class OAuthError(Exception):
    """Custom exception for OAuth-related errors."""
    def __init__(self, message: str, provider: str = None, original_exception: Exception = None):
        super().__init__(message)
        self.provider = provider
        self.original_exception = original_exception
        self.message = message

    def __str__(self):
        error_str = f"OAuth Error: {self.message}"
        if self.provider:
            error_str = f"[{self.provider}] {error_str}"
        if self.original_exception:
            error_str += f" (Original error: {type(self.original_exception).__name__}: {str(self.original_exception)})"
        return error_str
