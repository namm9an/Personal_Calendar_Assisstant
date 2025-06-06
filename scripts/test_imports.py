#!/usr/bin/env python3
"""
Test script to verify imports and Python path setup.
"""

import os
import sys
from pathlib import Path

def main():
    # Print current Python path
    print("Current Python path:")
    for path in sys.path:
        print(f"  - {path}")
        
    # Try to import app module
    try:
        import app
        print("\nSuccessfully imported app module")
        print(f"App module location: {app.__file__}")
    except ImportError as e:
        print(f"\nFailed to import app module: {e}")
        
    # Try to import specific modules
    try:
        from app.core.secrets_manager import get_secrets_manager
        print("Successfully imported get_secrets_manager")
    except ImportError as e:
        print(f"Failed to import get_secrets_manager: {e}")
        
    try:
        from app.core.config.secrets_config import secrets_config
        print("Successfully imported secrets_config")
    except ImportError as e:
        print(f"Failed to import secrets_config: {e}")

if __name__ == "__main__":
    main() 