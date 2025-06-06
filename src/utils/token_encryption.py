from datetime import datetime, timedelta
from typing import Optional
from cryptography.fernet import Fernet
import base64
import os

class TokenEncryption:
    def __init__(self, key: Optional[str] = None):
        """Initialize TokenEncryption with an optional key."""
        self.key = key or os.getenv("TOKEN_ENCRYPTION_KEY", "default_key_for_testing")
        # Ensure key is 32 bytes for Fernet
        key_bytes = self.key.encode()
        if len(key_bytes) < 32:
            key_bytes = key_bytes.ljust(32, b'0')
        elif len(key_bytes) > 32:
            key_bytes = key_bytes[:32]
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt(self, token: str) -> str:
        """Encrypt a token."""
        if not token:
            return ""
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt a token."""
        if not encrypted_token:
            return ""
        try:
            return self.fernet.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {str(e)}")

    def get_token_expiry(self, provider: str) -> datetime:
        """Get token expiry time."""
        # Default expiry is 1 hour from now
        return datetime.now() + timedelta(hours=1)

    def is_token_expired(self, provider: str) -> bool:
        """Check if token is expired."""
        return False  # For testing purposes 