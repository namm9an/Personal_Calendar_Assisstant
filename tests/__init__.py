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

# Get POSTGRES_URL from environment
postgres_url = f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"

# Check if POSTGRES components are set
if not all([os.environ.get('POSTGRES_USER'), os.environ.get('POSTGRES_PASSWORD'), 
            os.environ.get('POSTGRES_HOST'), os.environ.get('POSTGRES_PORT'), 
            os.environ.get('POSTGRES_DB')]):
    raise ValueError(
        "Error: The Postgres environment variables are not set correctly. "
        "Please ensure they are defined in your .env file (e.g., .env in the project root) "
        "and that load_dotenv() is working correctly. "
        "The .env file should contain variables like: \n"
        "POSTGRES_USER=postgres\n"
        "POSTGRES_PASSWORD=yourpassword\n"
        "POSTGRES_DB=calendar_assistant\n"
        "POSTGRES_HOST=localhost\n"
        "POSTGRES_PORT=5433"
    )

# Set SQLAlchemy URL from the environment variable
config.set_main_option("sqlalchemy.url", postgres_url)

# Interpret the config file for Python logging.
# ... (rest of the file) ...