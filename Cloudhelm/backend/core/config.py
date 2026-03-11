"""
Configuration management using Pydantic Settings.
All configuration values are loaded from environment variables.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # General
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_origin: str = Field(..., alias="FRONTEND_ORIGIN")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Auth / JWT
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expires_minutes: int = Field(
        default=60, 
        alias="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
    )
    
    # OAuth - GitHub
    github_client_id: str = Field(..., alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(..., alias="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(..., alias="GITHUB_REDIRECT_URI")
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")  # Optional PAT for Release Impact
    
    # OAuth - Google
    google_client_id: str = Field(..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(..., alias="GOOGLE_REDIRECT_URI")
    
    # AI - Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    
    # AI - Mistral
    mistral_api_key: Optional[str] = Field(default=None, alias="MISTRAL_API_KEY")
    
    class Config:
        # Look for .env file in the backend directory
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()
