#!/usr/bin/env python3
"""
Secret rotation script for the calendar assistant.
This script helps rotate all secrets and encryption keys.
"""
import os
import base64
import json
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet

def generate_new_key() -> str:
    """Generate a new Fernet key."""
    return Fernet.generate_key().decode()

def backup_current_secrets():
    """Backup current secrets to a timestamped file."""
    env_file = Path(".env")
    if not env_file.exists():
        print("No .env file found to backup")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f".env.backup_{timestamp}")
    
    with open(env_file) as src, open(backup_file, "w") as dst:
        dst.write(src.read())
    print(f"Backed up current secrets to {backup_file}")

def rotate_secrets():
    """Rotate all secrets and encryption keys."""
    # Backup current secrets
    backup_current_secrets()
    
    # Generate new keys
    new_keys = {
        "TOKEN_ENCRYPTION_KEY": generate_new_key(),
        "JWT_SECRET_KEY": base64.b64encode(os.urandom(32)).decode(),
        "API_KEY": base64.b64encode(os.urandom(32)).decode(),
        "ENCRYPTION_KEY": base64.b64encode(os.urandom(32)).decode()
    }
    
    # Update .env file
    env_file = Path(".env")
    with open(env_file, "w") as f:
        for key, value in new_keys.items():
            f.write(f"{key}={value}\n")
    
    print("Successfully rotated all secrets")
    print("\nIMPORTANT: You need to:")
    print("1. Update your Kubernetes secrets")
    print("2. Restart your application")
    print("3. Re-encrypt any stored tokens with the new key")

if __name__ == "__main__":
    rotate_secrets() 