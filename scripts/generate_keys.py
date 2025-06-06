#!/usr/bin/env python3
"""
Generate secure keys for the application.
This script generates all required encryption keys and secrets.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_fernet_key() -> str:
    """Generate a secure Fernet key."""
    return Fernet.generate_key().decode()

def generate_secret_key() -> str:
    """Generate a secure secret key for JWT signing."""
    return base64.b64encode(os.urandom(32)).decode()

def generate_api_key() -> str:
    """Generate a secure API key."""
    return base64.b64encode(os.urandom(32)).decode()

def main():
    """Generate all required keys and print them."""
    print("Generating secure keys...")
    print("\n=== PRODUCTION KEYS ===")
    print(f"TOKEN_ENCRYPTION_KEY={generate_fernet_key()}")
    print(f"JWT_SECRET_KEY={generate_secret_key()}")
    print(f"API_KEY={generate_api_key()}")
    
    print("\n=== TEST KEYS ===")
    print(f"TEST_TOKEN_ENCRYPTION_KEY={generate_fernet_key()}")
    print(f"TEST_JWT_SECRET_KEY={generate_secret_key()}")
    print(f"TEST_API_KEY={generate_api_key()}")
    
    print("\nIMPORTANT: Add these keys to your .env file and rotate any existing keys!")

if __name__ == "__main__":
    main() 