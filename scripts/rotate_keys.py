#!/usr/bin/env python3
"""
Script to handle key rotation for the secrets management system.
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.secrets_manager import get_secrets_manager
from app.core.config.secrets_config import secrets_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KeyRotationManager:
    def __init__(self):
        self.secrets_manager = get_secrets_manager()
        self.rotation_history_file = Path("secrets/rotation_history.json")
        self.rotation_history_file.parent.mkdir(exist_ok=True)
        
    def load_rotation_history(self) -> Dict[str, Any]:
        """Load rotation history from file."""
        if not self.rotation_history_file.exists():
            return {}
            
        try:
            with open(self.rotation_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading rotation history: {str(e)}")
            return {}
            
    def save_rotation_history(self, history: Dict[str, Any]) -> None:
        """Save rotation history to file."""
        try:
            with open(self.rotation_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rotation history: {str(e)}")
            
    def backup_key(self, key: str, value: str) -> bool:
        """Backup a key before rotation."""
        backup_key = f"{key}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.secrets_manager.set_secret(backup_key, value)
        
    def check_rotation_needed(self, key: str) -> bool:
        """Check if a key needs rotation based on history."""
        history = self.load_rotation_history()
        key_history = history.get(key, {})
        
        if not key_history:
            return True
            
        last_rotation = datetime.datetime.fromisoformat(key_history.get('last_rotation', '2000-01-01'))
        rotation_interval = datetime.timedelta(days=30)  # 30 days rotation interval
        
        return datetime.datetime.now() - last_rotation > rotation_interval
        
    def rotate_key(self, key: str, force: bool = False) -> bool:
        """Rotate a key if needed."""
        if not force and not self.check_rotation_needed(key):
            logger.info(f"Key {key} does not need rotation yet")
            return True
            
        try:
            # Get current value
            current_value = self.secrets_manager.get_secret(key)
            if not current_value:
                logger.error(f"Key {key} not found")
                return False
                
            # Backup current value
            if not self.backup_key(key, current_value):
                logger.error(f"Failed to backup key {key}")
                return False
                
            # Generate new value (implement your key generation logic here)
            new_value = self.generate_new_key(key)
            
            # Set new value
            if not self.secrets_manager.set_secret(key, new_value):
                logger.error(f"Failed to set new value for key {key}")
                return False
                
            # Update rotation history
            history = self.load_rotation_history()
            history[key] = {
                'last_rotation': datetime.datetime.now().isoformat(),
                'backup_key': f"{key}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            self.save_rotation_history(history)
            
            logger.info(f"Successfully rotated key {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating key {key}: {str(e)}")
            return False
            
    def generate_new_key(self, key: str) -> str:
        """Generate a new key value."""
        # Implement your key generation logic here
        # This is a placeholder that generates a random string
        import secrets
        return secrets.token_urlsafe(32)
        
    def rotate_all_keys(self, force: bool = False) -> bool:
        """Rotate all keys that need rotation."""
        keys_to_rotate = [
            "TOKEN_ENCRYPTION_KEY",
            "JWT_SECRET_KEY",
            "API_KEY",
            "ENCRYPTION_KEY"
        ]
        
        success = True
        for key in keys_to_rotate:
            if not self.rotate_key(key, force):
                success = False
                logger.error(f"Failed to rotate key {key}")
                
        return success

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rotate encryption keys")
    parser.add_argument("--force", action="store_true", help="Force rotation of all keys")
    args = parser.parse_args()
    
    rotation_manager = KeyRotationManager()
    
    if args.force:
        logger.info("Forcing rotation of all keys...")
    else:
        logger.info("Checking keys that need rotation...")
        
    success = rotation_manager.rotate_all_keys(force=args.force)
    
    if success:
        logger.info("Key rotation completed successfully")
    else:
        logger.error("Key rotation failed")
        exit(1)

if __name__ == "__main__":
    main() 