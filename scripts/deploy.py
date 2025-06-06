#!/usr/bin/env python3
"""
Deployment script for the calendar assistant.
Handles all setup steps including key generation, environment setup, and validation.
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import base64
from cryptography.fernet import Fernet

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def generate_fernet_key() -> str:
    return Fernet.generate_key().decode()

def generate_secret_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

def create_env_file():
    """Create .env file with generated keys."""
    env_file = Path(".env")
    if env_file.exists():
        print("Backing up existing .env file...")
        backup_file = env_file.with_suffix('.env.backup')
        env_file.rename(backup_file)
    
    print("Creating new .env file...")
    with open(env_file, "w") as f:
        # Production keys
        f.write("# Production Keys\n")
        f.write(f"TOKEN_ENCRYPTION_KEY={generate_fernet_key()}\n")
        f.write(f"JWT_SECRET_KEY={generate_secret_key()}\n")
        f.write(f"API_KEY={generate_secret_key()}\n")
        f.write(f"ENCRYPTION_KEY={generate_secret_key()}\n\n")
        
        # Test keys
        f.write("# Test Keys\n")
        f.write(f"TEST_TOKEN_ENCRYPTION_KEY={generate_fernet_key()}\n")
        f.write(f"TEST_JWT_SECRET_KEY={generate_secret_key()}\n")
        f.write(f"TEST_API_KEY={generate_secret_key()}\n\n")
        
        # Database configuration
        f.write("# Database Configuration\n")
        f.write("DB_HOST=localhost\n")
        f.write("DB_PORT=5432\n")
        f.write("DB_NAME=calendar_assistant\n")
        f.write("DB_USER=calendar_assistant\n")
        f.write("DB_PASSWORD=change_me_in_production\n")
    
    print("Created new .env file with generated keys")
    
    # Load the new environment variables
    load_dotenv(env_file)

def setup_database():
    """Set up the database."""
    print("Setting up database...")
    try:
        # Run database migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running database migrations: {e}")
        sys.exit(1)

def validate_setup():
    """Validate the setup."""
    print("Validating setup...")
    from scripts.validate_env import validate_environment
    is_valid, errors = validate_environment()
    if not is_valid:
        print("Setup validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("Setup validation passed!")

def main():
    """Main deployment function."""
    print("Starting deployment...")
    
    # Create environment file
    create_env_file()
    
    # Validate setup
    validate_setup()
    
    # Setup database
    setup_database()
    
    print("\nDeployment completed successfully!")
    print("\nNext steps:")
    print("1. Review the generated .env file")
    print("2. Update any default values as needed")
    print("3. Start the application with: python scripts/startup.py")

if __name__ == "__main__":
    main() 