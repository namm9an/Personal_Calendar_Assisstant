from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# This is the Alembic Config object
config = context.config

# Get database connection details from environment variables
postgres_user = os.getenv("POSTGRES_USER", "postgres")
postgres_password = os.getenv("POSTGRES_PASSWORD", "")
# Check if running in Docker container (/.dockerenv exists in Docker)
is_docker = os.path.exists('/.dockerenv')
# Default to "postgres" in Docker, "localhost" otherwise
default_host = "postgres" if is_docker else "localhost"
postgres_host = os.getenv("POSTGRES_HOST", default_host)
postgres_port = os.getenv("POSTGRES_PORT", "5432")
postgres_db = os.getenv("POSTGRES_DB", "postgres")

# Construct the database URL
database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

# Set SQLAlchemy URL
config.set_main_option("sqlalchemy.url", database_url)

# Set up Python loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models
from app.models.user import User
from app.models.calendar import CalendarAction, UserCalendar
from app.db.postgres import Base
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()