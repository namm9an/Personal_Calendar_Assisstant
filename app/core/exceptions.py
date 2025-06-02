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
