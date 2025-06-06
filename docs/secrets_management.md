# Secrets Management System

This document describes the secrets management system used in the Personal Calendar Assistant project.

## Overview

The secrets management system provides a secure way to store and manage sensitive information such as encryption keys, API keys, and other credentials. It supports multiple providers:

- Local (encrypted file storage)
- AWS Secrets Manager
- HashiCorp Vault
- Google Cloud Secret Manager

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-secrets.txt
```

### 2. Configure Environment

Create a `.env` file with the following configuration:

```env
# Secrets Management Configuration
SECRETS_PROVIDER=local  # or aws, vault, google

# AWS Configuration (if using AWS)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Vault Configuration (if using Vault)
VAULT_URL=http://localhost:8200
VAULT_TOKEN=your_vault_token

# Google Cloud Configuration (if using Google Cloud)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### 3. Initialize the System

```bash
# For local storage
python scripts/setup_secrets.py --provider local

# For AWS
python scripts/setup_secrets.py --provider aws

# For Vault
python scripts/setup_secrets.py --provider vault

# For Google Cloud
python scripts/setup_secrets.py --provider google
```

## Usage

### Basic Usage

```python
from app.core.secrets_manager import get_secrets_manager

# Get the secrets manager instance
secrets_manager = get_secrets_manager()

# Store a secret
secrets_manager.set_secret("API_KEY", "your-api-key")

# Retrieve a secret
api_key = secrets_manager.get_secret("API_KEY")
```

### Key Rotation

The system includes a key rotation mechanism to regularly update encryption keys:

```bash
# Check if keys need rotation
python scripts/rotate_keys.py

# Force rotation of all keys
python scripts/rotate_keys.py --force
```

### Migration

To migrate secrets from the old system to the new one:

```bash
# Dry run first
python scripts/migrate_secrets.py --dry-run

# Perform migration
python scripts/migrate_secrets.py --verify
```

## Security Considerations

1. **Local Storage**:
   - Secrets are encrypted before storage
   - The `secrets` directory is git-ignored
   - Encryption keys are stored securely

2. **Cloud Providers**:
   - Use IAM roles and policies
   - Enable encryption at rest
   - Use secure communication channels

3. **Key Rotation**:
   - Keys are rotated every 30 days
   - Old keys are backed up before rotation
   - Rotation history is maintained

## Best Practices

1. **Never commit secrets to version control**
2. **Use environment variables for provider configuration**
3. **Regularly rotate encryption keys**
4. **Monitor access to secrets**
5. **Use the appropriate provider for your environment**

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**:
   ```bash
   $env:PYTHONHTTPSVERIFY=0; pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements-secrets.txt
   ```

2. **Provider Connection Issues**:
   - Check credentials and permissions
   - Verify network connectivity
   - Check provider-specific logs

3. **Key Rotation Failures**:
   - Check rotation history
   - Verify backup creation
   - Check provider quotas

## API Reference

### SecretsManager

```python
class SecretsManager:
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret value."""
        
    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret value."""
        
    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
```

### Configuration

```python
class SecretsConfig:
    ENVIRONMENT: str
    SECRETS_PROVIDER: str
    AWS_REGION: str
    AWS_ACCESS_KEY_ID: SecretStr
    AWS_SECRET_ACCESS_KEY: SecretStr
    VAULT_URL: str
    VAULT_TOKEN: SecretStr
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_APPLICATION_CREDENTIALS: str
```

## Contributing

1. Follow the project's coding standards
2. Add tests for new features
3. Update documentation
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 