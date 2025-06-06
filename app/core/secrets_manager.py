import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
import boto3
from botocore.exceptions import ClientError
import hvac
from google.cloud import secretmanager

class SecretsManager:
    """Base class for secrets management."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value."""
        raise NotImplementedError

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret value."""
        raise NotImplementedError

    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        raise NotImplementedError

class LocalSecretsManager(SecretsManager):
    """Local file-based secrets manager for development."""
    def __init__(self, secrets_dir: str = "secrets"):
        super().__init__()
        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(exist_ok=True)
        self.encryption_key = os.getenv("SECRETS_ENCRYPTION_KEY")
        if self.encryption_key:
            self.cipher_suite = Fernet(self.encryption_key.encode())

    def _encrypt(self, value: str) -> str:
        """Encrypt a value if encryption is enabled."""
        if not self.encryption_key:
            return value
        return self.cipher_suite.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt a value if encryption is enabled."""
        if not self.encryption_key:
            return value
        return self.cipher_suite.decrypt(value.encode()).decode()

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret from local storage."""
        try:
            file_path = self.secrets_dir / f"{key}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                return self._decrypt(data['value'])
        except Exception as e:
            self.logger.error(f"Error getting secret {key}: {str(e)}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in local storage."""
        try:
            file_path = self.secrets_dir / f"{key}.json"
            data = {
                'value': self._encrypt(value),
                'updated_at': str(datetime.now())
            }
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error setting secret {key}: {str(e)}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from local storage."""
        try:
            file_path = self.secrets_dir / f"{key}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting secret {key}: {str(e)}")
            return False

class AWSSecretsManager(SecretsManager):
    """AWS Secrets Manager implementation."""
    def __init__(self, region_name: str = None):
        super().__init__()
        self.client = boto3.client('secretsmanager', region_name=region_name)

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=key)
            return response['SecretString']
        except ClientError as e:
            self.logger.error(f"Error getting secret {key}: {str(e)}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in AWS Secrets Manager."""
        try:
            self.client.create_secret(
                Name=key,
                SecretString=value
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                self.client.update_secret(
                    SecretId=key,
                    SecretString=value
                )
                return True
            self.logger.error(f"Error setting secret {key}: {str(e)}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from AWS Secrets Manager."""
        try:
            self.client.delete_secret(
                SecretId=key,
                ForceDeleteWithoutRecovery=True
            )
            return True
        except ClientError as e:
            self.logger.error(f"Error deleting secret {key}: {str(e)}")
            return False

class VaultSecretsManager(SecretsManager):
    """HashiCorp Vault implementation."""
    def __init__(self, url: str, token: str):
        super().__init__()
        self.client = hvac.Client(url=url, token=token)

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret from Vault."""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=key)
            return response['data']['data']['value']
        except Exception as e:
            self.logger.error(f"Error getting secret {key}: {str(e)}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in Vault."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=key,
                secret={'value': value}
            )
            return True
        except Exception as e:
            self.logger.error(f"Error setting secret {key}: {str(e)}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from Vault."""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=key)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting secret {key}: {str(e)}")
            return False

class GoogleSecretsManager(SecretsManager):
    """Google Cloud Secret Manager implementation."""
    def __init__(self, project_id: str):
        super().__init__()
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret from Google Cloud Secret Manager."""
        try:
            name = f"projects/{self.project_id}/secrets/{key}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            self.logger.error(f"Error getting secret {key}: {str(e)}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in Google Cloud Secret Manager."""
        try:
            parent = f"projects/{self.project_id}"
            secret_id = key
            
            try:
                self.client.get_secret(request={"name": f"{parent}/secrets/{secret_id}"})
            except Exception:
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            
            self.client.add_secret_version(
                request={
                    "parent": f"{parent}/secrets/{secret_id}",
                    "payload": {"data": value.encode("UTF-8")},
                }
            )
            return True
        except Exception as e:
            self.logger.error(f"Error setting secret {key}: {str(e)}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from Google Cloud Secret Manager."""
        try:
            name = f"projects/{self.project_id}/secrets/{key}"
            self.client.delete_secret(request={"name": name})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting secret {key}: {str(e)}")
            return False

def get_secrets_manager() -> SecretsManager:
    """Factory function to get the appropriate secrets manager based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        provider = os.getenv("SECRETS_PROVIDER", "aws").lower()
        
        if provider == "aws":
            return AWSSecretsManager(region_name=os.getenv("AWS_REGION"))
        elif provider == "vault":
            return VaultSecretsManager(
                url=os.getenv("VAULT_URL"),
                token=os.getenv("VAULT_TOKEN")
            )
        elif provider == "google":
            return GoogleSecretsManager(
                project_id=os.getenv("GOOGLE_CLOUD_PROJECT")
            )
        else:
            raise ValueError(f"Unsupported secrets provider: {provider}")
    
    return LocalSecretsManager()

# Usage example:
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Get the appropriate secrets manager
    secrets_manager = get_secrets_manager()
    
    # Example usage
    secrets_manager.set_secret("API_KEY", "test-key")
    api_key = secrets_manager.get_secret("API_KEY")
    print(f"Retrieved API key: {api_key}") 