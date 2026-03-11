"""
Database connection and session management with optimized pooling.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator

from backend.core.config import settings

# Create SQLAlchemy engine with optimized connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,  # Increased pool size for concurrent requests
    max_overflow=40,  # Allow up to 60 total connections
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Disable SQL logging for performance
    connect_args={
        "connect_timeout": 10
    }
)

# Enable query result caching at connection level
@event.listens_for(engine, "connect")
def set_connection_optimizations(dbapi_conn, connection_record):
    """Set connection-level optimizations (Neon-compatible)."""
    try:
        cursor = dbapi_conn.cursor()
        # Set statement timeout using SET command (Neon-compatible)
        cursor.execute("SET statement_timeout = '30s'")
        cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
        cursor.close()
    except Exception:
        # Silently fail if database doesn't support these settings
        pass

# Create SessionLocal class with optimized settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent unnecessary queries after commit
)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    Optimized for fast connection reuse.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
