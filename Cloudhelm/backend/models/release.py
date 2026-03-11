"""
Release-related models for tracking software deployments and their impact.
"""
import uuid
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.db import Base


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class Repository(Base):
    """Tracks GitHub repositories for release monitoring."""
    
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    full_name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    stars = Column(Integer, default=0)
    owner = Column(String, nullable=False)
    github_id = Column(Integer, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_deployment = Column(DateTime(timezone=True), nullable=True)
    is_syncing = Column(Boolean, default=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    releases = relationship("Release", back_populates="repository", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_repository_owner_name', 'owner', 'name'),
    )
    
    def __repr__(self):
        return f"<Repository(id={self.id}, full_name={self.full_name})>"


class Release(Base):
    """Tracks software release deployments."""
    
    __tablename__ = "releases"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    repo_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    service = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    commit = Column(String, nullable=False)
    branch = Column(String, default="main")
    deployed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String, default="success")  # success, failed, pending
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="Healthy")  # Healthy, Suspect, Risky
    deployment_duration = Column(Integer, nullable=True)  # in seconds
    triggered_by = Column(String, nullable=True)
    workflow_run_id = Column(String, unique=True, nullable=True)
    github_run_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="releases")
    anomalies = relationship("ReleaseAnomaly", back_populates="release", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_release_deployed_at_status', 'deployed_at', 'status'),
        Index('idx_release_service_deployed_at', 'service', 'deployed_at'),
    )
    
    def __repr__(self):
        return f"<Release(id={self.id}, service={self.service}, version={self.version})>"


class ReleaseAnomaly(Base):
    """Tracks anomalies detected during or after a release."""
    
    __tablename__ = "release_anomalies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    release_id = Column(String, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    severity = Column(String, default="low")  # low, medium, high, critical
    value = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False)
    deviation = Column(Float, nullable=False)  # percentage
    anomaly_type = Column(String, default="metric")  # metric, cost
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    release = relationship("Release", back_populates="anomalies")
    
    __table_args__ = (
        Index('idx_release_anomaly_release_severity', 'release_id', 'severity'),
    )
    
    def __repr__(self):
        return f"<ReleaseAnomaly(id={self.id}, metric={self.metric_name}, severity={self.severity})>"


class ReleaseIncident(Base):
    """Links incidents to releases for correlation analysis."""
    
    __tablename__ = "release_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(String, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    correlation_score = Column(Float, default=1.0)  # 0-1, how strongly correlated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_release_incident_unique', 'release_id', 'incident_id', unique=True),
    )
    
    def __repr__(self):
        return f"<ReleaseIncident(release_id={self.release_id}, incident_id={self.incident_id})>"
