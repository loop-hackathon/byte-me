"""
Pydantic schemas for health monitoring API.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


# Request Schemas

class ServiceRegisterRequest(BaseModel):
    """Schema for registering a new service."""
    service_name: str = Field(..., description="Service name")
    service_type: str = Field(..., description="Service type (microservice, database, cache, etc.)")


class DemoDataRequest(BaseModel):
    """Schema for generating demo data."""
    hours: int = Field(24, ge=1, le=168, description="Hours of historical data to generate")
    services: Optional[List[str]] = Field(None, description="List of service names (defaults to demo services)")
    anomaly_rate: float = Field(0.05, ge=0.0, le=1.0, description="Probability of injecting anomalies")


# Response Schemas

class LatencyResponse(BaseModel):
    """Schema for latency metrics."""
    p50: float = Field(..., description="50th percentile latency in ms")
    p95: float = Field(..., description="95th percentile latency in ms")
    p99: float = Field(..., description="99th percentile latency in ms")


class ResourcesResponse(BaseModel):
    """Schema for resource usage."""
    cpu: float = Field(..., description="CPU usage percentage")
    memory: float = Field(..., description="Memory usage percentage")


class HealthSummaryResponse(BaseModel):
    """Schema for health summary response."""
    service_name: str
    timestamp: str
    request_rate: float
    error_rate: float
    latency: LatencyResponse
    resources: ResourcesResponse
    restart_count: int
    pod_count: int
    health_score: float
    status: str  # 'healthy', 'degraded', 'warning', 'critical'
    
    class Config:
        from_attributes = True


class AnomalyResponse(BaseModel):
    """Schema for anomaly response."""
    id: str
    service_name: str
    timestamp: str
    anomaly_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    anomaly_score: float
    affected_metrics: List[str]
    description: str
    
    class Config:
        from_attributes = True


class MetricHistoryResponse(BaseModel):
    """Schema for historical metrics response."""
    timestamp: str
    request_rate: float
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    cpu_usage: float
    memory_usage: float
    restart_count: int
    pod_count: int
    
    class Config:
        from_attributes = True


class ServiceResponse(BaseModel):
    """Schema for service response."""
    id: str
    service_name: str
    service_type: str
    status: str
    last_seen: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class ContainerResponse(BaseModel):
    """Schema for container response."""
    container_id: str
    container_name: str
    image: str
    status: str
    created: str
    ports: List[str]


class ContainerStatsResponse(BaseModel):
    """Schema for container statistics response."""
    container_id: str
    container_name: str
    timestamp: str
    cpu_percent: float
    memory_usage_bytes: int
    memory_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    disk_read_bytes: int
    disk_write_bytes: int
    pids: int


class PodResponse(BaseModel):
    """Schema for Kubernetes pod response."""
    name: str
    namespace: str
    phase: str
    ready_containers: int
    total_containers: int
    restart_count: int
    node_name: Optional[str]
    created: Optional[str]


class DeploymentResponse(BaseModel):
    """Schema for Kubernetes deployment response."""
    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    updated_replicas: int
    created: Optional[str]


class NodeStats(BaseModel):
    """Schema for node statistics."""
    total: int
    ready: int
    not_ready: int


class PodStats(BaseModel):
    """Schema for pod statistics."""
    total: int
    running: int
    pending: int
    failed: int


class ClusterHealthResponse(BaseModel):
    """Schema for cluster health response."""
    nodes: NodeStats
    pods: PodStats
    namespaces: int


class DemoDataResponse(BaseModel):
    """Schema for demo data generation response."""
    services: int
    metrics_generated: int
    anomalies_injected: int
    hours: int
    message: str


class InfrastructureAvailability(BaseModel):
    """Schema for infrastructure availability status."""
    docker_available: bool
    kubernetes_available: bool
