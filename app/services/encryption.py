"""
Token encryption service for OAuth credentials.
"""
import os
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional

from app.config import get_settings
from app.core.exceptions import EncryptionError

settings = get_settings()


class TokenEncryption:
    """Service for encrypting and decrypting OAuth tokens."""
    
    def __init__(self, key: Optional[str] = None):
        """Initialize encryption service with the Fernet key."""
        if key:
            self.fernet = Fernet(key.encode())
        elif os.getenv('TESTING', '').lower() == 'true':
            self.fernet = Fernet(b'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=')
        else:
            self.fernet = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    
    def encrypt(self, token: str) -> str:
        """
        Encrypt a token string.
        
        Args:
            token: Plain text token to encrypt
            
        Returns:
            Encrypted token as string
            
        Raises:
            EncryptionError: If token is None or encryption fails
        """
        if token is None:
            raise EncryptionError("Token cannot be None")
        
        try:
            # Encrypt the token and return as string
            return self.fernet.encrypt(token.encode()).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt token: {str(e)}")
    
    def decrypt(self, encrypted_token: str) -> str:
        """
        Decrypt an encrypted token.
        
        Args:
            encrypted_token: Encrypted token to decrypt
            
        Returns:
            Decrypted token as string
            
        Raises:
            EncryptionError: If token is None or decryption fails
        """
        if encrypted_token is None:
            raise EncryptionError("Token cannot be None")
        
        try:
            # Decrypt the token and return as string
            return self.fernet.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            raise EncryptionError("Invalid token format")
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt token: {str(e)}")
