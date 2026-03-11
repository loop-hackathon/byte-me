"""
User model for authentication.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from backend.core.db import Base


class User(Base):
    """User model for storing OAuth authenticated users."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # "github" or "google"
    provider_id = Column(String, nullable=False)  # External user ID from provider
    email = Column(String, nullable=True)  # May be null if GitHub user hides email
    name = Column(String, nullable=True)
    github_access_token = Column(Text, nullable=True)  # Store GitHub OAuth token
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Create unique constraint on provider + provider_id
    __table_args__ = (
        {'schema': None},
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, provider={self.provider}, email={self.email})>"
