"""Tests for token encryption service."""
import pytest
from datetime import datetime, timedelta
from src.utils.token_encryption import TokenEncryption
from src.core.exceptions import EncryptionError
from cryptography.fernet import Fernet

@pytest.fixture
def token_encryption():
    """Create a token encryption service."""
    return TokenEncryption.get_instance()

class TestTokenEncryption:
    """Tests for TokenEncryption."""

    def test_encrypt_decrypt(self, token_encryption):
        """Test token encryption and decryption."""
        # Test data
        test_token = "test-access-token"
        
        # Encrypt token
        encrypted = TokenEncryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = TokenEncryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_special_chars(self, token_encryption):
        """Test encryption/decryption with special characters."""
        # Test data with special characters
        test_token = "token!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        # Encrypt token
        encrypted = TokenEncryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        
        # Decrypt token
        decrypted = TokenEncryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_unicode(self, token_encryption):
        """Test encryption/decryption with unicode characters."""
        # Test data with unicode characters
        test_token = "täst-tøkéñ-üñîçødê-😀"
        
        # Encrypt token
        encrypted = TokenEncryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        
        # Decrypt token
        decrypted = TokenEncryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_long_token(self, token_encryption):
        """Test encryption/decryption with a long token."""
        # Generate a long token (1000 characters)
        test_token = "x" * 1000
        
        # Encrypt token
        encrypted = TokenEncryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        
        # Decrypt token
        decrypted = TokenEncryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_null_and_empty_strings(self, token_encryption):
        """Test encryption/decryption of null and empty strings."""
        # Test with None
        encrypted_none = TokenEncryption.encrypt(None)
        assert encrypted_none == ""
        
        # Test with empty string
        encrypted_empty = TokenEncryption.encrypt("")
        assert encrypted_empty == ""
        
        # Decrypt empty string should return empty string
        decrypted_empty = TokenEncryption.decrypt("")
        assert decrypted_empty == ""

    def test_encrypt_decrypt_with_invalid_encrypted_token(self, token_encryption):
        """Test decryption with invalid encrypted token."""
        # Invalid token
        invalid_token = "invalid-token"
        
        # Attempt to decrypt invalid token should raise error
        with pytest.raises(EncryptionError):
            TokenEncryption.decrypt(invalid_token)

    def test_encrypt_decrypt_with_different_keys(self):
        """Test encryption/decryption with different keys."""
        # Create two encryption services with different keys
        # Generate two valid Fernet keys
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        
        # Create a new instance with key1
        encryption1 = TokenEncryption(key1)
        
        # Test data
        test_token = "test-token"
        
        # Encrypt with first key using the instance method
        encrypted = encryption1.encrypt_instance(test_token)
        
        # Create a second instance with key2
        encryption2 = TokenEncryption(key2)
        
        # Try to decrypt with the second instance - should fail with EncryptionError
        with pytest.raises(EncryptionError):
            encryption2.decrypt_instance(encrypted)

    def test_encrypt_decrypt_with_same_key_different_instances(self):
        """Test encryption/decryption with same key but different instances."""
        # Generate a valid Fernet key
        key = Fernet.generate_key().decode()
        
        # Create two instances with the same key
        encryption1 = TokenEncryption(key)
        encryption2 = TokenEncryption(key)
        
        # Test data
        test_token = "test-token"
        
        # Encrypt with first instance
        encrypted = encryption1.encrypt_instance(test_token)
        
        # Decrypt with second instance - should work
        decrypted = encryption2.decrypt_instance(encrypted)
        
        # Verify decryption
        assert decrypted == test_token 