from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from src.db.test_config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    
    # Google OAuth fields
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)
    
    # Microsoft OAuth fields
    microsoft_access_token = Column(String, nullable=True)
    microsoft_refresh_token = Column(String, nullable=True)
    microsoft_token_expiry = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 