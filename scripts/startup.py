#!/usr/bin/env python3
"""
Startup script for the calendar assistant.
Validates environment and generates keys if needed.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.validate_env import validate_environment
from scripts.generate_keys import generate_fernet_key, generate_secret_key, generate_api_key

def ensure_env_file():
    """Ensure .env file exists with all required variables."""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating new .env file...")
        with open(env_file, "w") as f:
            # Generate production keys
            f.write("# Production Keys\n")
            f.write(f"TOKEN_ENCRYPTION_KEY={generate_fernet_key()}\n")
            f.write(f"JWT_SECRET_KEY={generate_secret_key()}\n")
            f.write(f"API_KEY={generate_api_key()}\n")
            f.write(f"ENCRYPTION_KEY={generate_secret_key()}\n\n")
            
            # Generate test keys
            f.write("# Test Keys\n")
            f.write(f"TEST_TOKEN_ENCRYPTION_KEY={generate_fernet_key()}\n")
            f.write(f"TEST_JWT_SECRET_KEY={generate_secret_key()}\n")
            f.write(f"TEST_API_KEY={generate_api_key()}\n\n")
            
            # Database configuration
            f.write("# Database Configuration\n")
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=5432\n")
            f.write("DB_NAME=calendar_assistant\n")
            f.write("DB_USER=calendar_assistant\n")
            f.write("DB_PASSWORD=change_me_in_production\n")
            
        print("Created new .env file with generated keys")
        print("IMPORTANT: Review and update the values in .env before proceeding!")

def main():
    """Main startup function."""
    print("Starting calendar assistant...")
    
    # Ensure .env file exists
    ensure_env_file()
    
    # Validate environment
    is_valid, errors = validate_environment()
    if not is_valid:
        print("Environment validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    
    print("Environment validation passed!")
    print("Starting application...")
    
    # Start the application
    os.system("uvicorn app.main:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main() 