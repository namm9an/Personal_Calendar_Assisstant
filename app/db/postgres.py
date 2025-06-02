"""
PostgreSQL database connection setup using SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.base import Base

# Import your models here so Base knows about them
# before create_all is called
from app.models import user # Assuming user.py contains User model
from app.models import calendar # Assuming calendar.py contains other calendar-related models
# If you have a central __init__.py in app.models that imports all models,
# you could potentially just do:
# import app.models

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create all tables in the database if they don't exist
# This should be called after Base is defined and models are imported
Base.metadata.create_all(bind=engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency to get a database session.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
