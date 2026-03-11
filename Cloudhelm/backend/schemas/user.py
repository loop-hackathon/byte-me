"""
Pydantic schemas for User-related API requests and responses.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: Optional[str] = None
    name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    provider: str
    provider_id: str


class UserResponse(UserBase):
    """Schema for user API responses."""
    id: int
    provider: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
