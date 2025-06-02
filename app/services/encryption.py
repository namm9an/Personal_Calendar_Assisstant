"""
Token encryption service for OAuth credentials.
"""
from cryptography.fernet import Fernet
from typing import Optional

from app.config import get_settings

settings = get_settings()


class TokenEncryption:
    """Service for encrypting and decrypting OAuth tokens."""
    
    def __init__(self):
        """Initialize encryption service with the Fernet key from settings."""
        self.fernet = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    
    def encrypt(self, token: str) -> Optional[str]:
        """
        Encrypt a token string.
        
        Args:
            token: Plain text token to encrypt
            
        Returns:
            Encrypted token as string, or None if input is empty
        """
        if not token:
            return None
        
        # Encrypt the token and return as string
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt an encrypted token.
        
        Args:
            encrypted_token: Encrypted token to decrypt
            
        Returns:
            Decrypted token as string, or None if input is empty
        """
        if not encrypted_token:
            return None
        
        # Decrypt the token and return as string
        return self.fernet.decrypt(encrypted_token.encode()).decode()
