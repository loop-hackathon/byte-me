"""
Pydantic schemas for release-related API requests and responses.
Adapted from Release-Impact-feature for CloudHelm.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Repository Schemas
class RepositoryBase(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    owner: str


class RepositoryCreate(RepositoryBase):
    github_id: int


class RepositoryResponse(RepositoryBase):
    id: str
    last_deployment: Optional[datetime] = None
    is_syncing: bool = False
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Release Schemas
class ReleaseBase(BaseModel):
    service: str
    version: str
    commit: str
    branch: str = "main"
    deployed_at: datetime
    status: str = "success"
    deployment_duration: Optional[int] = None
    triggered_by: Optional[str] = None


class ReleaseCreate(ReleaseBase):
    repo_id: str
    workflow_run_id: Optional[str] = None
    github_run_number: Optional[int] = None


class ReleaseResponse(ReleaseBase):
    id: str
    repo_id: str
    risk_score: float
    risk_level: str
    
    class Config:
        from_attributes = True


# Anomaly Schemas
class AnomalyBase(BaseModel):
    metric_name: str
    timestamp: datetime
    severity: str
    value: float
    expected_value: float
    deviation: float
    type: str = "metric"


class AnomalyCreate(AnomalyBase):
    release_id: str


class AnomalyResponse(AnomalyBase):
    id: str
    release_id: str
    
    class Config:
        from_attributes = True


# Security Metrics Schemas
class SecurityMetrics(BaseModel):
    """Vulnerability counts from a Trivy scan."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unknown: int = 0


class SecurityImpact(BaseModel):
    """Security scan result embedded in the release impact response."""
    risk_score: float = 0.0
    security_metrics: SecurityMetrics = SecurityMetrics()
    scan_status: str = "not_run"   # not_run | success | failed | skipped


# Impact Analysis Response
class ReleaseImpactResponse(BaseModel):
    release_id: str
    risk_score: float
    risk_level: str
    anomaly_count: dict
    incident_count: int
    cost_delta: dict
    anomalies: List[dict]
    incidents: List[dict]
    metrics_before_after: List[dict] = []
    security: SecurityImpact = SecurityImpact()


# Sync Request
class SyncRequest(BaseModel):
    owner: str
    repo: str
