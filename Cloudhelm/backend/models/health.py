"""
Health monitoring models for service health tracking and anomaly detection.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index, UniqueConstraint
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from backend.core.db import Base


class ServiceMetric(Base):
    """Service health metrics collected over time."""
    
    __tablename__ = "service_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    service_name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    request_rate = Column(Float, nullable=False, default=0.0)
    error_rate = Column(Float, nullable=False, default=0.0)
    latency_p50 = Column(Float, nullable=False, default=0.0)
    latency_p95 = Column(Float, nullable=False, default=0.0)
    latency_p99 = Column(Float, nullable=False, default=0.0)
    cpu_usage = Column(Float, nullable=False, default=0.0)
    memory_usage = Column(Float, nullable=False, default=0.0)
    restart_count = Column(Integer, nullable=False, default=0)
    pod_count = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('service_name', 'timestamp', name='uq_service_metrics_service_timestamp'),
        Index('idx_service_metrics_service_timestamp', 'service_name', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ServiceMetric(service={self.service_name}, timestamp={self.timestamp}, error_rate={self.error_rate})>"


class MetricsAnomaly(Base):
    """Detected anomalies in service metrics."""
    
    __tablename__ = "metrics_anomalies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    service_name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    anomaly_type = Column(String(100), nullable=False)  # 'metric_deviation', 'cost', etc.
    severity = Column(String(50), nullable=False, index=True)  # 'low', 'medium', 'high', 'critical'
    anomaly_score = Column(Float, nullable=False)
    affected_metrics = Column(Text, nullable=False)  # JSON array of metric names
    description = Column(Text, nullable=False)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_metrics_anomalies_service_severity', 'service_name', 'severity'),
        Index('idx_metrics_anomalies_timestamp_severity', 'timestamp', 'severity'),
    )
    
    def __repr__(self):
        return f"<MetricsAnomaly(service={self.service_name}, severity={self.severity}, score={self.anomaly_score})>"


class Service(Base):
    """Service registry for health monitoring."""
    
    __tablename__ = "services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    service_name = Column(String(255), nullable=False, unique=True, index=True)
    service_type = Column(String(100), nullable=False)  # 'microservice', 'database', 'cache', etc.
    status = Column(String(50), nullable=False, default='active')  # 'active', 'inactive'
    last_seen = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Service(name={self.service_name}, type={self.service_type}, status={self.status})>"


class ContainerMetric(Base):
    """Docker container metrics for infrastructure monitoring."""
    
    __tablename__ = "container_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    container_id = Column(String(255), nullable=False, index=True)
    container_name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    cpu_percent = Column(Float, nullable=False, default=0.0)
    memory_usage_bytes = Column(Integer, nullable=False, default=0)
    memory_percent = Column(Float, nullable=False, default=0.0)
    network_rx_bytes = Column(Integer, nullable=False, default=0)
    network_tx_bytes = Column(Integer, nullable=False, default=0)
    disk_read_bytes = Column(Integer, nullable=False, default=0)
    disk_write_bytes = Column(Integer, nullable=False, default=0)
    pids = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_container_metrics_container_timestamp', 'container_id', 'timestamp'),
        Index('idx_container_metrics_name_timestamp', 'container_name', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ContainerMetric(container={self.container_name}, timestamp={self.timestamp}, cpu={self.cpu_percent}%)>"


class PodMetric(Base):
    """Kubernetes pod metrics for cluster monitoring."""
    
    __tablename__ = "pod_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    pod_name = Column(String(255), nullable=False, index=True)
    namespace = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    phase = Column(String(50), nullable=False)  # 'Running', 'Pending', 'Failed', etc.
    ready_containers = Column(Integer, nullable=False, default=0)
    total_containers = Column(Integer, nullable=False, default=0)
    restart_count = Column(Integer, nullable=False, default=0)
    node_name = Column(String(255), nullable=True)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_pod_metrics_pod_timestamp', 'pod_name', 'timestamp'),
        Index('idx_pod_metrics_namespace_timestamp', 'namespace', 'timestamp'),
        Index('idx_pod_metrics_namespace_pod', 'namespace', 'pod_name'),
    )
    
    def __repr__(self):
        return f"<PodMetric(pod={self.pod_name}, namespace={self.namespace}, phase={self.phase})>"
