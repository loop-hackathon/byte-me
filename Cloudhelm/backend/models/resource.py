"""
Resource efficiency models for tracking cloud resource utilization and recommendations.
Adapted from Loop_ResourceDashboard for CloudHelm.
"""
import uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.db import Base


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class Resource(Base):
    """Tracks cloud resources (VMs, containers, etc.) for efficiency monitoring."""
    
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)  # vm, container, database, etc.
    team = Column(String, nullable=False, index=True)
    environment = Column(String, nullable=False, index=True)  # production, staging, development
    waste_score = Column(Float, default=0.0, index=True)  # 0-100, higher = more waste
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    metrics = relationship("ResourceMetric", back_populates="resource", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="resource", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_resource_team_env', 'team', 'environment'),
        Index('idx_resource_waste_score', 'waste_score'),
    )
    
    def __repr__(self):
        return f"<Resource(id={self.id}, name={self.name}, waste_score={self.waste_score})>"


class ResourceMetric(Base):
    """Tracks time-series metrics for resource utilization."""
    
    __tablename__ = "resource_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    cpu_utilization = Column(Float, nullable=False)  # 0-100
    memory_utilization = Column(Float, nullable=False)  # 0-100
    disk_io = Column(Float, nullable=True)  # MB/s
    network_io = Column(Float, nullable=True)  # MB/s
    
    # Relationships
    resource = relationship("Resource", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_metric_resource_timestamp', 'resource_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ResourceMetric(id={self.id}, resource_id={self.resource_id}, timestamp={self.timestamp})>"


class Recommendation(Base):
    """Tracks optimization recommendations for resources."""
    
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type = Column(String, nullable=False, index=True)  # rightsizing, schedule
    description = Column(Text, nullable=False)
    potential_savings = Column(Float, nullable=False)  # Monthly savings in USD
    suggested_action = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8)  # 0-1, confidence in recommendation
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    resource = relationship("Resource", back_populates="recommendations")
    
    __table_args__ = (
        Index('idx_recommendation_type', 'recommendation_type'),
        Index('idx_recommendation_resource_type', 'resource_id', 'recommendation_type'),
    )
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, type={self.recommendation_type}, savings=${self.potential_savings})>"
