"""
Incident models for CloudHelm.
Tracks production incidents with AI-powered summaries.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from backend.core.db import Base


class IncidentStatus(str, enum.Enum):
    """Incident status enum"""
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class IncidentSeverity(str, enum.Enum):
    """Incident severity enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(Base):
    """Incident model"""
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(String, unique=True, nullable=False, index=True)
    
    # Basic info
    service_name = Column(String, nullable=False, index=True)
    environment = Column(String, nullable=False, index=True)
    status = Column(SQLEnum(IncidentStatus), nullable=False, default=IncidentStatus.INVESTIGATING)
    severity = Column(SQLEnum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamps
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Incident details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    anomalies = Column(Text, nullable=True)
    metrics_summary = Column(Text, nullable=True)
    cost_changes = Column(Text, nullable=True)
    
    # AI-generated summary
    ai_summary = Column(Text, nullable=True)
    summary_generated_at = Column(DateTime, nullable=True)
    
    # Related release (optional)
    related_release_id = Column(UUID(as_uuid=True), ForeignKey("releases.id"), nullable=True)
    related_release = relationship("Release", back_populates="incidents")
    
    def __repr__(self):
        return f"<Incident {self.incident_id} - {self.service_name} ({self.status})>"
