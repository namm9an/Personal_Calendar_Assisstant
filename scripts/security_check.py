import os
import secrets
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Dict, List, Tuple
import json
import re
from datetime import datetime

class SecurityManager:
    def __init__(self):
        self.project_root = Path(".")
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"
        self.secrets_dir = self.project_root / "secrets"
        self.backup_dir = self.project_root / "secrets_backup"

    def check_for_exposed_secrets(self) -> List[Tuple[str, str]]:
        """Check git history and files for exposed secrets."""
        exposed_secrets = []
        
        # Check for common secret patterns in files
        secret_patterns = [
            r'password\s*=\s*["\']([^"\']+)["\']',
            r'secret\s*=\s*["\']([^"\']+)["\']',
            r'key\s*=\s*["\']([^"\']+)["\']',
            r'token\s*=\s*["\']([^"\']+)["\']',
            r'api_key\s*=\s*["\']([^"\']+)["\']',
            r'auth\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in secret_patterns:
            for file in self.project_root.rglob("*"):
                if file.is_file() and not any(x in str(file) for x in ['.git', 'node_modules', '__pycache__']):
                    try:
                        content = file.read_text()
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            exposed_secrets.append((str(file), match.group(0)))
                    except Exception:
                        continue
        
        return exposed_secrets

    def generate_secure_keys(self) -> Dict[str, str]:
        """Generate new secure keys for all required services."""
        keys = {
            "TOKEN_ENCRYPTION_KEY": Fernet.generate_key().decode(),
            "JWT_SECRET_KEY": secrets.token_urlsafe(32),
            "API_KEY": secrets.token_urlsafe(32),
            "ENCRYPTION_KEY": secrets.token_urlsafe(32),
            "TEST_TOKEN_ENCRYPTION_KEY": Fernet.generate_key().decode(),
            "TEST_JWT_SECRET_KEY": secrets.token_urlsafe(32),
            "TEST_API_KEY": secrets.token_urlsafe(32),
            "TEST_ENCRYPTION_KEY": secrets.token_urlsafe(32)
        }
        return keys

    def backup_current_secrets(self):
        """Backup current secrets before rotation."""
        if not self.env_file.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(exist_ok=True)
        backup_file = self.backup_dir / f"env_backup_{timestamp}"
        
        with open(self.env_file, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())

    def rotate_keys(self):
        """Rotate all keys and update .env file."""
        self.backup_current_secrets()
        new_keys = self.generate_secure_keys()
        
        # Read current .env file
        current_env = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        current_env[key] = value
        
        # Update with new keys
        current_env.update(new_keys)
        
        # Write back to .env
        with open(self.env_file, 'w') as f:
            for key, value in current_env.items():
                f.write(f"{key}={value}\n")

    def setup_secure_secrets(self):
        """Set up a more secure secrets management system."""
        # Create secrets directory
        self.secrets_dir.mkdir(exist_ok=True)
        
        # Create separate files for different types of secrets
        secret_files = {
            "encryption_keys.json": ["TOKEN_ENCRYPTION_KEY", "ENCRYPTION_KEY"],
            "auth_keys.json": ["JWT_SECRET_KEY", "API_KEY"],
            "test_keys.json": ["TEST_TOKEN_ENCRYPTION_KEY", "TEST_JWT_SECRET_KEY", 
                             "TEST_API_KEY", "TEST_ENCRYPTION_KEY"]
        }
        
        # Read current .env
        current_env = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        current_env[key] = value
        
        # Create separate files for each category
        for filename, keys in secret_files.items():
            secrets = {k: current_env.get(k, "") for k in keys}
            with open(self.secrets_dir / filename, 'w') as f:
                json.dump(secrets, f, indent=2)

def main():
    security = SecurityManager()
    
    print("\n=== Checking for Exposed Secrets ===")
    exposed = security.check_for_exposed_secrets()
    if exposed:
        print("\nWARNING: Found potential exposed secrets:")
        for file, secret in exposed:
            print(f"\nFile: {file}")
            print(f"Secret: {secret}")
    else:
        print("No exposed secrets found!")
    
    print("\n=== Rotating Keys ===")
    security.rotate_keys()
    print("Keys rotated successfully!")
    
    print("\n=== Setting up Secure Secrets Management ===")
    security.setup_secure_secrets()
    print("Secure secrets management system set up!")
    
    print("\n=== Next Steps ===")
    print("1. Review the exposed secrets (if any) and remove them from git history")
    print("2. Update your .env file with the new keys")
    print("3. Update your deployment configuration to use the new secrets management system")
    print("4. Consider using a secrets manager service (AWS Secrets Manager, HashiCorp Vault) for production")

if __name__ == "__main__":
    main() 