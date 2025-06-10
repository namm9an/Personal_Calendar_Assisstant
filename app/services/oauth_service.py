"""
OAuth service for handling authentication and token management.
"""
from datetime import datetime, timedelta
from typing import Dict, Any

# In-memory storage for OAuth states during testing
oauth_states: Dict[str, Dict[str, Any]] = {}

class OAuthService:
    """Base OAuth service."""
    
    @staticmethod
    def is_token_expired(expiry_time: datetime) -> bool:
        """
        Check if a token is expired.
        
        Args:
            expiry_time: Token expiry time
            
        Returns:
            True if token is expired, False otherwise
        """
        return expiry_time <= datetime.utcnow()
    
    @staticmethod
    def calculate_expiry_time(expires_in: int) -> datetime:
        """
        Calculate token expiry time from expires_in seconds.
        
        Args:
            expires_in: Token expiration in seconds
            
        Returns:
            Expiry time as datetime
        """
        return datetime.utcnow() + timedelta(seconds=expires_in) 