#!/usr/bin/env python3
"""
Script to migrate secrets to the new secrets management system.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from app.core.secrets_manager import get_secrets_manager
from app.core.config.secrets_config import secrets_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_current_secrets() -> Dict[str, str]:
    """Load secrets from current .env file."""
    load_dotenv()
    
    # List of secret keys to migrate
    secret_keys = [
        "TOKEN_ENCRYPTION_KEY",
        "JWT_SECRET_KEY",
        "API_KEY",
        "ENCRYPTION_KEY",
        "TEST_TOKEN_ENCRYPTION_KEY",
        "TEST_JWT_SECRET_KEY",
        "TEST_API_KEY",
        "TEST_ENCRYPTION_KEY"
    ]
    
    return {key: os.getenv(key) for key in secret_keys if os.getenv(key)}

def migrate_secrets(secrets: Dict[str, str], dry_run: bool = False) -> bool:
    """Migrate secrets to the new secrets management system."""
    secrets_manager = get_secrets_manager()
    
    try:
        for key, value in secrets.items():
            if not value:
                continue
                
            logger.info(f"Migrating secret: {key}")
            
            if not dry_run:
                success = secrets_manager.set_secret(key, value)
                if not success:
                    logger.error(f"Failed to migrate secret: {key}")
                    return False
                
        return True
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False

def verify_migration(secrets: Dict[str, str]) -> bool:
    """Verify that secrets were migrated correctly."""
    secrets_manager = get_secrets_manager()
    
    try:
        for key, original_value in secrets.items():
            if not original_value:
                continue
                
            migrated_value = secrets_manager.get_secret(key)
            if not migrated_value:
                logger.error(f"Secret not found after migration: {key}")
                return False
                
            if migrated_value != original_value:
                logger.error(f"Secret value mismatch for: {key}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return False

def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate secrets to new management system")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    parser.add_argument("--verify", action="store_true", help="Verify migration after completion")
    args = parser.parse_args()
    
    # Load current secrets
    logger.info("Loading current secrets...")
    secrets = load_current_secrets()
    
    if not secrets:
        logger.warning("No secrets found to migrate")
        return
    
    logger.info(f"Found {len(secrets)} secrets to migrate")
    
    # Perform migration
    if args.dry_run:
        logger.info("Performing dry run...")
        success = migrate_secrets(secrets, dry_run=True)
    else:
        logger.info("Starting migration...")
        success = migrate_secrets(secrets)
    
    if not success:
        logger.error("Migration failed")
        return
    
    # Verify migration if requested
    if args.verify and not args.dry_run:
        logger.info("Verifying migration...")
        if verify_migration(secrets):
            logger.info("Migration verified successfully")
        else:
            logger.error("Migration verification failed")
            return
    
    logger.info("Migration completed successfully")

if __name__ == "__main__":
    main() 