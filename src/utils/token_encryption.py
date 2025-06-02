from cryptography.fernet import Fernet, InvalidToken
import os
from datetime import datetime, timedelta

class TokenEncryption:
    def __init__(self):
        # Use a valid base64-encoded 32-byte key for tests if not set in env
        default_key = b'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY='  # base64 for b'0123456789abcdef0123456789abcdef'
        key = os.getenv('ENCRYPTION_KEY')
        if key:
            self.key = key.encode() if isinstance(key, str) else key
        else:
            self.key = default_key
        self.cipher_suite = Fernet(self.key)

    def encrypt(self, token: str) -> str:
        if not token:
            return None
        return self.cipher_suite.encrypt(token.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        if not encrypted_token:
            return None
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()

    def get_token_expiry(self, provider: str) -> datetime:
        """Get token expiry time (1 hour from now for testing)"""
        return datetime.utcnow() + timedelta(hours=1) 