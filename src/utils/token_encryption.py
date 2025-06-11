from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
import base64
import os
from src.core.exceptions import EncryptionError

# Singleton instance
_instance = None

class TokenEncryption:
    """Service for encrypting and decrypting OAuth tokens."""
    
    def __init__(self, key: Optional[str] = None):
        """Initialize encryption service with the Fernet key."""
        self.key = key or os.getenv("TOKEN_ENCRYPTION_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")
        
        # Handle different key formats
        if isinstance(self.key, str):
            try:
                # Try to use the key directly
                self.fernet = Fernet(self.key.encode())
            except Exception:
                # If that fails, try to pad it to 32 bytes
                key_bytes = self.key.encode()
                if len(key_bytes) < 32:
                    key_bytes = key_bytes.ljust(32, b'0')
                elif len(key_bytes) > 32:
                    key_bytes = key_bytes[:32]
                self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
        else:
            # If key is already bytes
            self.fernet = Fernet(self.key)
    
    @classmethod
    def get_instance(cls, key: Optional[str] = None) -> 'TokenEncryption':
        """Get the singleton instance of TokenEncryption."""
        global _instance
        if _instance is None:
            _instance = cls(key)
        return _instance
    
    @classmethod
    def encrypt(cls, token: str) -> str:
        """
        Class method to encrypt a token string.
        
        Args:
            token: Plain text token to encrypt
            
        Returns:
            Encrypted token as string
        """
        if token is None or token == "":
            return ""
        
        instance = cls.get_instance()
        try:
            # Encrypt the token and return as string
            return instance.fernet.encrypt(token.encode()).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt token: {str(e)}")
    
    @classmethod
    def decrypt(cls, encrypted_token: str) -> str:
        """
        Class method to decrypt an encrypted token.
        
        Args:
            encrypted_token: Encrypted token to decrypt
            
        Returns:
            Decrypted token as string
        """
        if encrypted_token is None or encrypted_token == "":
            return ""
        
        instance = cls.get_instance()
        try:
            # Decrypt the token and return as string
            return instance.fernet.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            raise EncryptionError("Invalid token format")
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt token: {str(e)}")
    
    def encrypt_instance(self, token: str) -> str:
        """Instance method to encrypt a token."""
        if token is None or token == "":
            return ""
        
        try:
            return self.fernet.encrypt(token.encode()).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt token: {str(e)}")
    
    def decrypt_instance(self, encrypted_token: str) -> str:
        """Instance method to decrypt a token."""
        if encrypted_token is None or encrypted_token == "":
            return ""
        
        try:
            return self.fernet.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            raise EncryptionError("Invalid token format")
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt token: {str(e)}")
    
    def get_token_expiry(self, provider: str) -> datetime:
        """Get token expiry time."""
        # Default expiry is 1 hour from now
        return datetime.now() + timedelta(hours=1)
    
    def is_token_expired(self, expiry: datetime) -> bool:
        """Check if token is expired."""
        if not expiry:
            return True
        return expiry < datetime.now() 