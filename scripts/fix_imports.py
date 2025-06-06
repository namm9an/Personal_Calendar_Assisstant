#!/usr/bin/env python3
"""
Script to fix Python import issues by creating necessary __init__.py files
and setting up the Python path correctly.
"""

import os
from pathlib import Path

def create_init_files():
    """Create __init__.py files in necessary directories."""
    directories = [
        "app",
        "app/core",
        "app/core/config",
        "app/services",
        "app/db",
        "app/models",
        "app/agent",
        "app/agents",
        "app/schemas",
        "app/api",
        "app/auth"
    ]
    
    for directory in directories:
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            print(f"Creating {init_file}")
            init_file.touch()
            
def main():
    """Main function."""
    print("Setting up Python package structure...")
    create_init_files()
    print("\nDone! Now try running the scripts again.")
    print("\nIf you still have issues, try running the scripts with:")
    print("PYTHONPATH=. python scripts/setup_secrets.py --provider local")

if __name__ == "__main__":
    main() 