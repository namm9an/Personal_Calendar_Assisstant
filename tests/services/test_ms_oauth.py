"""
Tests for Microsoft OAuth service.
"""
import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from msal import SerializableTokenCache
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.ms_oauth import MicrosoftOAuthService
from app.services.encryption import TokenEncryption


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_user():
    """Mock user with Microsoft credentials."""
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.microsoft_access_token = "encrypted-access-token"
    user.microsoft_refresh_token = "encrypted-refresh-token"
    user.microsoft_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    return user


@pytest.fixture
def mock_token_encryption():
    """Mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "decrypted-token"
    return encryption


@pytest.fixture
def ms_oauth_service(mock_db, mock_token_encryption):
    """Create a Microsoft OAuth service with mocked dependencies."""
    with patch("app.services.ms_oauth.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.ms_oauth.settings") as mock_settings:
            mock_settings.ms_client_id = "test-client-id"
            mock_settings.ms_client_secret = "test-client-secret"
            mock_settings.ms_tenant_id = "test-tenant-id"
            mock_settings.ms_redirect_uri = "http://localhost:8000/auth/ms/callback"
            mock_settings.token_encryption_key = "test-encryption-key"
            service = MicrosoftOAuthService(mock_db)
            return service


class TestMicrosoftOAuthService:
    """Tests for MicrosoftOAuthService."""

    def test_generate_auth_url(self, ms_oauth_service):
        """Test generating authorization URL."""
        # Test
        auth_url = ms_oauth_service.get_authorization_url()

        # Verify
        assert "https://login.microsoftonline.com/" in auth_url
        assert "client_id=test-client-id" in auth_url
        assert "redirect_uri=http" in auth_url
        assert "state=" in auth_url

    def test_save_state(self, ms_oauth_service, mock_db):
        """Test saving state to database."""
        # Setup
        state = "test-state"
        user_id = "test-user-id"

        # Test
        ms_oauth_service.save_state(state, user_id)

        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_validate_state_valid(self, ms_oauth_service, mock_db):
        """Test validating a valid state."""
        # Setup
        mock_state = MagicMock()
        mock_state.state = "test-state"
        mock_state.user_id = "test-user-id"
        mock_state.created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state

        # Test
        result = ms_oauth_service.validate_state("test-state")

        # Verify
        assert result == "test-user-id"
        mock_db.delete.assert_called_once_with(mock_state)
        mock_db.commit.assert_called_once()

    def test_validate_state_invalid(self, ms_oauth_service, mock_db):
        """Test validating an invalid state."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc_info:
            ms_oauth_service.validate_state("invalid-state")

        # Verify
        assert exc_info.value.status_code == 400
        assert "Invalid or expired state" in exc_info.value.detail

    def test_validate_state_expired(self, ms_oauth_service, mock_db):
        """Test validating an expired state."""
        # Setup
        mock_state = MagicMock()
        mock_state.state = "test-state"
        mock_state.user_id = "test-user-id"
        mock_state.created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state

        # Test
        with pytest.raises(HTTPException) as exc_info:
            ms_oauth_service.validate_state("test-state")

        # Verify
        assert exc_info.value.status_code == 400
        assert "Invalid or expired state" in exc_info.value.detail
        mock_db.delete.assert_called_once_with(mock_state)
        mock_db.commit.assert_called_once()

    @patch("app.services.ms_oauth.ConfidentialClientApplication")
    def test_get_token(self, mock_msal_app, ms_oauth_service, mock_db, mock_user):
        """Test getting token successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
            "id_token_claims": {"preferred_username": "test@example.com"}
        }

        # Test
        ms_oauth_service.get_token("test-code", "test-user-id")

        # Verify
        mock_app_instance.acquire_token_by_authorization_code.assert_called_once()
        mock_db.commit.assert_called_once()
        assert mock_user.microsoft_access_token == "encrypted-token"
        assert mock_user.microsoft_refresh_token == "encrypted-token"
        assert mock_user.microsoft_token_expiry is not None

    @patch("app.services.ms_oauth.ConfidentialClientApplication")
    def test_get_token_error(self, mock_msal_app, ms_oauth_service, mock_db, mock_user):
        """Test getting token with error."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_authorization_code.return_value = {
            "error": "invalid_grant",
            "error_description": "AADSTS70000: Invalid authorization code"
        }

        # Test
        with pytest.raises(HTTPException) as exc_info:
            ms_oauth_service.get_token("test-code", "test-user-id")

        # Verify
        assert exc_info.value.status_code == 400
        assert "Failed to get token" in exc_info.value.detail

    def test_get_token_user_not_found(self, ms_oauth_service, mock_db):
        """Test getting token when user not found."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc_info:
            ms_oauth_service.get_token("test-code", "non-existent-user")

        # Verify
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail
