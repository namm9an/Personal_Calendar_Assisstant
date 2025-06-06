"""
Test package for Personal Calendar Assistant.
"""
import os
from dotenv import load_dotenv
from alembic.config import Config

# Load environment variables from .env file
load_dotenv()

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = Config()

# Use SQLite for tests
sqlite_url = "sqlite:///:memory:"

# Set SQLAlchemy URL for tests
config.set_main_option("sqlalchemy.url", sqlite_url)

# Interpret the config file for Python logging.
# ... (rest of the file) ...