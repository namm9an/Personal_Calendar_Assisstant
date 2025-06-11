"""
Token encryption service for OAuth credentials.
"""
import os
from typing import Optional

from src.utils.token_encryption import TokenEncryption
from app.core.exceptions import EncryptionError 