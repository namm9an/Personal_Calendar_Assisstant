from typing import Dict, Any
from pydantic import BaseSettings, SecretStr

class SecretsConfig(BaseSettings):
    """Configuration for secrets management."""
    
    # Environment
    ENVIRONMENT: str = "development"
    SECRETS_PROVIDER: str = "local"
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: SecretStr = None
    AWS_SECRET_ACCESS_KEY: SecretStr = None
    
    # Vault Configuration
    VAULT_URL: str = "http://localhost:8200"
    VAULT_TOKEN: SecretStr = None
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str = None
    GOOGLE_APPLICATION_CREDENTIALS: str = None
    
    # Local Secrets Configuration
    SECRETS_DIR: str = "secrets"
    SECRETS_ENCRYPTION_KEY: SecretStr = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT.lower() == "testing"
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get configuration for the selected secrets provider."""
        provider = self.SECRETS_PROVIDER.lower()
        
        if provider == "aws":
            return {
                "region_name": self.AWS_REGION,
                "aws_access_key_id": self.AWS_ACCESS_KEY_ID.get_secret_value() if self.AWS_ACCESS_KEY_ID else None,
                "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY.get_secret_value() if self.AWS_SECRET_ACCESS_KEY else None
            }
        elif provider == "vault":
            return {
                "url": self.VAULT_URL,
                "token": self.VAULT_TOKEN.get_secret_value() if self.VAULT_TOKEN else None
            }
        elif provider == "google":
            return {
                "project_id": self.GOOGLE_CLOUD_PROJECT,
                "credentials_path": self.GOOGLE_APPLICATION_CREDENTIALS
            }
        elif provider == "local":
            return {
                "secrets_dir": self.SECRETS_DIR,
                "encryption_key": self.SECRETS_ENCRYPTION_KEY.get_secret_value() if self.SECRETS_ENCRYPTION_KEY else None
            }
        else:
            raise ValueError(f"Unsupported secrets provider: {provider}")

# Create a singleton instance
secrets_config = SecretsConfig() 