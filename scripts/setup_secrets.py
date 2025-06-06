#!/usr/bin/env python3
"""
Script to help with initial setup of the secrets management system.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import logging
import secrets
from app.core.secrets_manager import get_secrets_manager
from app.core.config.secrets_config import secrets_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_initial_keys() -> Dict[str, str]:
    """Generate initial encryption keys."""
    return {
        "TOKEN_ENCRYPTION_KEY": secrets.token_urlsafe(32),
        "JWT_SECRET_KEY": secrets.token_urlsafe(32),
        "API_KEY": secrets.token_urlsafe(32),
        "ENCRYPTION_KEY": secrets.token_urlsafe(32),
        "TEST_TOKEN_ENCRYPTION_KEY": secrets.token_urlsafe(32),
        "TEST_JWT_SECRET_KEY": secrets.token_urlsafe(32),
        "TEST_API_KEY": secrets.token_urlsafe(32),
        "TEST_ENCRYPTION_KEY": secrets.token_urlsafe(32)
    }

def setup_local_secrets() -> bool:
    """Set up local secrets storage."""
    try:
        # Create secrets directory
        secrets_dir = Path("secrets")
        secrets_dir.mkdir(exist_ok=True)
        
        # Create .gitignore to prevent committing secrets
        gitignore_path = secrets_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write("*\n!.gitignore\n")
                
        return True
    except Exception as e:
        logger.error(f"Error setting up local secrets: {str(e)}")
        return False

def setup_aws_secrets() -> bool:
    """Set up AWS Secrets Manager."""
    try:
        # Check AWS credentials
        if not secrets_config.AWS_ACCESS_KEY_ID or not secrets_config.AWS_SECRET_ACCESS_KEY:
            logger.error("AWS credentials not configured")
            return False
            
        # Test AWS connection
        secrets_manager = get_secrets_manager()
        if not secrets_manager:
            logger.error("Failed to initialize AWS Secrets Manager")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error setting up AWS secrets: {str(e)}")
        return False

def setup_vault_secrets() -> bool:
    """Set up HashiCorp Vault."""
    try:
        # Check Vault configuration
        if not secrets_config.VAULT_URL or not secrets_config.VAULT_TOKEN:
            logger.error("Vault configuration not complete")
            return False
            
        # Test Vault connection
        secrets_manager = get_secrets_manager()
        if not secrets_manager:
            logger.error("Failed to initialize Vault client")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error setting up Vault secrets: {str(e)}")
        return False

def setup_google_secrets() -> bool:
    """Set up Google Cloud Secret Manager."""
    try:
        # Check Google Cloud configuration
        if not secrets_config.GOOGLE_CLOUD_PROJECT:
            logger.error("Google Cloud project not configured")
            return False
            
        # Test Google Cloud connection
        secrets_manager = get_secrets_manager()
        if not secrets_manager:
            logger.error("Failed to initialize Google Cloud Secret Manager")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error setting up Google Cloud secrets: {str(e)}")
        return False

def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up secrets management system")
    parser.add_argument("--provider", choices=["local", "aws", "vault", "google"], 
                      default="local", help="Secrets provider to use")
    args = parser.parse_args()
    
    # Set up provider-specific configuration
    if args.provider == "local":
        if not setup_local_secrets():
            logger.error("Failed to set up local secrets")
            exit(1)
    elif args.provider == "aws":
        if not setup_aws_secrets():
            logger.error("Failed to set up AWS secrets")
            exit(1)
    elif args.provider == "vault":
        if not setup_vault_secrets():
            logger.error("Failed to set up Vault secrets")
            exit(1)
    elif args.provider == "google":
        if not setup_google_secrets():
            logger.error("Failed to set up Google Cloud secrets")
            exit(1)
    
    # Generate and store initial keys
    logger.info("Generating initial encryption keys...")
    keys = generate_initial_keys()
    
    secrets_manager = get_secrets_manager()
    for key, value in keys.items():
        if not secrets_manager.set_secret(key, value):
            logger.error(f"Failed to store key: {key}")
            exit(1)
            
    logger.info("Successfully set up secrets management system")
    
    # Create .env file with provider configuration
    env_content = f"""# Secrets Management Configuration
SECRETS_PROVIDER={args.provider}

# AWS Configuration (if using AWS)
AWS_REGION={secrets_config.AWS_REGION}
AWS_ACCESS_KEY_ID={secrets_config.AWS_ACCESS_KEY_ID.get_secret_value() if secrets_config.AWS_ACCESS_KEY_ID else ''}
AWS_SECRET_ACCESS_KEY={secrets_config.AWS_SECRET_ACCESS_KEY.get_secret_value() if secrets_config.AWS_SECRET_ACCESS_KEY else ''}

# Vault Configuration (if using Vault)
VAULT_URL={secrets_config.VAULT_URL}
VAULT_TOKEN={secrets_config.VAULT_TOKEN.get_secret_value() if secrets_config.VAULT_TOKEN else ''}

# Google Cloud Configuration (if using Google Cloud)
GOOGLE_CLOUD_PROJECT={secrets_config.GOOGLE_CLOUD_PROJECT}
GOOGLE_APPLICATION_CREDENTIALS={secrets_config.GOOGLE_APPLICATION_CREDENTIALS}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
        
    logger.info("Created .env file with provider configuration")

if __name__ == "__main__":
    main() 