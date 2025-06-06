import secrets
from cryptography.fernet import Fernet
import base64

def generate_keys():
    # Generate Fernet key
    fernet_key = Fernet.generate_key().decode()
    
    # Generate URL-safe keys
    secret_key = secrets.token_urlsafe(32)
    encryption_key = secrets.token_urlsafe(32)
    
    print("\n=== Generated Keys ===")
    print(f"TOKEN_ENCRYPTION_KEY={fernet_key}")
    print(f"JWT_SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print("\n=== Test Keys ===")
    print(f"TEST_TOKEN_ENCRYPTION_KEY={Fernet.generate_key().decode()}")
    print(f"TEST_JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
    print(f"TEST_ENCRYPTION_KEY={secrets.token_urlsafe(32)}")

if __name__ == "__main__":
    generate_keys() 