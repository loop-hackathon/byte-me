"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.db import get_db, Base
from core.config import settings

# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-key-for-testing-only")
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "database_url", SQLALCHEMY_DATABASE_URL)
    return settings


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "github_id": 12345,
        "username": "testuser",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://github.com/testuser.png",
        "is_active": True,
    }


@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing."""
    return {
        "id": "repo-123",
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "description": "A test repository",
        "language": "Python",
        "stars": 10,
        "private": False,
        "owner_id": 1,
    }


@pytest.fixture
def sample_release_data():
    """Sample release data for testing."""
    return {
        "id": "release-123",
        "repository_id": "repo-123",
        "version": "1.0.0",
        "commit": "abc123def456",
        "deployed_at": "2024-01-01T12:00:00Z",
        "status": "success",
        "risk_level": "Healthy",
        "risk_score": 25.0,
        "triggered_by": "testuser",
    }