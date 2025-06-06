#!/usr/bin/env python3
"""
Environment variable validation script.
Validates all required environment variables are present and properly formatted.
"""
import os
import sys
import base64
from typing import Dict, List, Tuple
from cryptography.fernet import Fernet

REQUIRED_VARS = {
    # Production variables
    "TOKEN_ENCRYPTION_KEY": {
        "description": "Fernet key for token encryption",
        "validate": lambda x: len(base64.b64decode(x)) == 32
    },
    "JWT_SECRET_KEY": {
        "description": "Secret key for JWT signing",
        "validate": lambda x: len(base64.b64decode(x)) >= 32
    },
    "API_KEY": {
        "description": "API key for external services",
        "validate": lambda x: len(base64.b64decode(x)) >= 32
    },
    "ENCRYPTION_KEY": {
        "description": "Key for general encryption",
        "validate": lambda x: len(base64.b64decode(x)) >= 32
    },
    
    # Database variables
    "DB_HOST": {
        "description": "Database host",
        "validate": lambda x: len(x) > 0
    },
    "DB_PORT": {
        "description": "Database port",
        "validate": lambda x: x.isdigit() and 0 < int(x) < 65536
    },
    "DB_NAME": {
        "description": "Database name",
        "validate": lambda x: len(x) > 0
    },
    "DB_USER": {
        "description": "Database user",
        "validate": lambda x: len(x) > 0
    },
    "DB_PASSWORD": {
        "description": "Database password",
        "validate": lambda x: len(x) >= 8
    },
    
    # Test variables (only required in test environment)
    "TEST_TOKEN_ENCRYPTION_KEY": {
        "description": "Test Fernet key for token encryption",
        "validate": lambda x: len(base64.b64decode(x)) == 32,
        "required_in_test": True
    },
    "TEST_JWT_SECRET_KEY": {
        "description": "Test secret key for JWT signing",
        "validate": lambda x: len(base64.b64decode(x)) >= 32,
        "required_in_test": True
    },
    "TEST_API_KEY": {
        "description": "Test API key for external services",
        "validate": lambda x: len(base64.b64decode(x)) >= 32,
        "required_in_test": True
    }
}

def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate all required environment variables.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    is_test = os.environ.get("ENVIRONMENT", "").lower() == "test"
    
    for var_name, config in REQUIRED_VARS.items():
        # Skip test variables if not in test environment
        if config.get("required_in_test") and not is_test:
            continue
            
        value = os.environ.get(var_name)
        if not value:
            errors.append(f"Missing required environment variable: {var_name} ({config['description']})")
            continue
            
        try:
            if not config["validate"](value):
                errors.append(f"Invalid format for {var_name}: {config['description']}")
        except Exception as e:
            errors.append(f"Error validating {var_name}: {str(e)}")
    
    return len(errors) == 0, errors

def main():
    """Main validation function."""
    is_valid, errors = validate_environment()
    
    if not is_valid:
        print("Environment validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    
    print("Environment validation passed!")
    sys.exit(0)

if __name__ == "__main__":
    main() 