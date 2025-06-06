"""Tests for token encryption service."""
import pytest
from datetime import datetime, timedelta
from app.services.encryption import TokenEncryption
from app.core.exceptions import EncryptionError

@pytest.fixture
def token_encryption():
    """Create a token encryption service."""
    return TokenEncryption("test-encryption-key")

class TestTokenEncryption:
    """Tests for TokenEncryption."""

    def test_encrypt_decrypt(self, token_encryption):
        """Test token encryption and decryption."""
        # Test data
        test_token = "test-access-token"
        
        # Encrypt token
        encrypted = token_encryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = token_encryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_special_chars(self, token_encryption):
        """Test encryption/decryption with special characters."""
        # Test data with special characters
        test_token = "test-token!@#$%^&*()_+{}|:<>?[]\\;',./"
        
        # Encrypt token
        encrypted = token_encryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = token_encryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_unicode(self, token_encryption):
        """Test encryption/decryption with Unicode characters."""
        # Test data with Unicode characters
        test_token = "test-token-测试-テスト-테스트"
        
        # Encrypt token
        encrypted = token_encryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = token_encryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_long_token(self, token_encryption):
        """Test encryption/decryption with a long token."""
        # Test data with a long token
        test_token = "x" * 1000  # 1000 characters
        
        # Encrypt token
        encrypted = token_encryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = token_encryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_empty_token(self, token_encryption):
        """Test encryption/decryption with an empty token."""
        # Test data with empty token
        test_token = ""
        
        # Encrypt token
        encrypted = token_encryption.encrypt(test_token)
        
        # Verify encryption
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = token_encryption.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token

    def test_encrypt_decrypt_with_none_token(self, token_encryption):
        """Test encryption/decryption with None token."""
        # Test data with None token
        test_token = None
        
        # Verify encryption raises error
        with pytest.raises(EncryptionError) as excinfo:
            token_encryption.encrypt(test_token)
        
        assert "Token cannot be None" in str(excinfo.value)
        
        # Verify decryption raises error
        with pytest.raises(EncryptionError) as excinfo:
            token_encryption.decrypt(test_token)
        
        assert "Token cannot be None" in str(excinfo.value)

    def test_encrypt_decrypt_with_invalid_encrypted_token(self, token_encryption):
        """Test decryption with invalid encrypted token."""
        # Test data with invalid encrypted token
        invalid_token = "invalid-encrypted-token"
        
        # Verify decryption raises error
        with pytest.raises(EncryptionError) as excinfo:
            token_encryption.decrypt(invalid_token)
        
        assert "Invalid token format" in str(excinfo.value)

    def test_encrypt_decrypt_with_different_keys(self):
        """Test encryption/decryption with different keys."""
        # Create two encryption services with different keys
        encryption1 = TokenEncryption("key1")
        encryption2 = TokenEncryption("key2")
        
        # Test data
        test_token = "test-token"
        
        # Encrypt with first key
        encrypted = encryption1.encrypt(test_token)
        
        # Verify decryption with different key raises error
        with pytest.raises(EncryptionError) as excinfo:
            encryption2.decrypt(encrypted)
        
        assert "Invalid token format" in str(excinfo.value)

    def test_encrypt_decrypt_with_same_key_different_instances(self):
        """Test encryption/decryption with same key but different instances."""
        # Create two encryption services with same key
        encryption1 = TokenEncryption("test-key")
        encryption2 = TokenEncryption("test-key")
        
        # Test data
        test_token = "test-token"
        
        # Encrypt with first instance
        encrypted = encryption1.encrypt(test_token)
        
        # Decrypt with second instance
        decrypted = encryption2.decrypt(encrypted)
        
        # Verify decryption
        assert decrypted == test_token 