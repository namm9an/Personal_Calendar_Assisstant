#!/usr/bin/env python3
"""
Manage Kubernetes secrets for the calendar assistant.
This script helps generate and update Kubernetes secrets.
"""
import os
import base64
import subprocess
from typing import Dict
from pathlib import Path

def encode_secret(value: str) -> str:
    """Encode a secret value in base64."""
    return base64.b64encode(value.encode()).decode()

def generate_secrets() -> Dict[str, str]:
    """Generate all required secrets."""
    return {
        "JWT_SECRET_KEY_BASE64": encode_secret(os.urandom(32).hex()),
        "TOKEN_ENCRYPTION_KEY_BASE64": encode_secret(os.urandom(32).hex()),
        "ENCRYPTION_KEY_BASE64": encode_secret(os.urandom(32).hex()),
        "API_KEY_BASE64": encode_secret(os.urandom(32).hex()),
        "DB_USER_BASE64": encode_secret("calendar_assistant"),
        "DB_PASSWORD_BASE64": encode_secret(os.urandom(16).hex()),
        "DB_NAME_BASE64": encode_secret("calendar_assistant")
    }

def update_k8s_secrets(secrets: Dict[str, str]):
    """Update Kubernetes secrets using kubectl."""
    # Create a temporary file with the secrets
    secrets_file = Path("k8s/secrets/temp-secrets.yaml")
    secrets_file.parent.mkdir(exist_ok=True)
    
    with open(secrets_file, "w") as f:
        f.write("apiVersion: v1\nkind: Secret\n")
        f.write("metadata:\n  name: calendar-assistant-secrets\n")
        f.write("type: Opaque\ndata:\n")
        for key, value in secrets.items():
            f.write(f"  {key}: {value}\n")
    
    try:
        # Apply the secrets
        subprocess.run(["kubectl", "apply", "-f", str(secrets_file)], check=True)
        print("Successfully updated Kubernetes secrets")
    except subprocess.CalledProcessError as e:
        print(f"Error updating Kubernetes secrets: {e}")
    finally:
        # Clean up
        secrets_file.unlink()

def main():
    """Generate and update Kubernetes secrets."""
    print("Generating new secrets...")
    secrets = generate_secrets()
    
    # Save secrets to .env file
    env_file = Path(".env")
    with open(env_file, "w") as f:
        for key, value in secrets.items():
            f.write(f"{key}={value}\n")
    print(f"Saved secrets to {env_file}")
    
    # Update Kubernetes secrets
    update_k8s_secrets(secrets)

if __name__ == "__main__":
    main() 