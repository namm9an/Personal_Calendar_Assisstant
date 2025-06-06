"""
Microsoft OAuth service stub for testing.
"""
from typing import Dict, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class MicrosoftOAuthService:
    """Stub for Microsoft OAuth service. Implement methods as needed for tests."""
    
    def __init__(self, db: Session):
        """Initialize the service with a database session."""
        self.db = db
        
    def save_state(self, state: str, user_id: str) -> None:
        """Save OAuth state to database."""
        pass
        
    def validate_state(self, state: str) -> str:
        """Validate OAuth state and return user ID."""
        pass
        
    def get_token(self, code: str, user_id: str) -> Dict:
        """Exchange authorization code for token."""
        pass
        
    def get_tokens(self, user_id: str) -> Tuple[str, str, str]:
        """Get access and refresh tokens for user."""
        pass 