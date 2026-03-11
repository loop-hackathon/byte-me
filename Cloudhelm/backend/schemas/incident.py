"""
Incident schemas for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class IncidentBase(BaseModel):
    """Base incident schema"""
    incident_id: str = Field(..., description="Unique incident identifier (e.g., INC-2024-001)")
    title: str = Field(..., description="Incident title")
    description: Optional[str] = Field(None, description="Detailed description")
    service: Optional[str] = Field(None, description="Affected service name")
    env: Optional[str] = Field(None, description="Environment (prod, staging, dev)")
    team: Optional[str] = Field(None, description="Responsible team")
    status: str = Field(..., description="Incident status (investigating, identified, monitoring, resolved)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    anomalies: Optional[str] = Field(None, description="Description of detected anomalies")
    recent_releases: Optional[str] = Field(None, description="Recent releases that may be related")
    metrics_summary: Optional[str] = Field(None, description="Summary of relevant metrics")
    cost_changes: Optional[str] = Field(None, description="Cost impact information")


class IncidentCreate(IncidentBase):
    """Schema for creating a new incident"""
    pass


class IncidentUpdate(BaseModel):
    """Schema for updating an incident"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    service: Optional[str] = None
    env: Optional[str] = None
    team: Optional[str] = None
    anomalies: Optional[str] = None
    recent_releases: Optional[str] = None
    metrics_summary: Optional[str] = None
    cost_changes: Optional[str] = None
    resolved_at: Optional[date] = None


class IncidentResponse(IncidentBase):
    """Schema for incident response"""
    id: int
    created_at: date
    resolved_at: Optional[date] = None
    ai_summary: Optional[str] = None
    summary_generated_at: Optional[date] = None
    
    class Config:
        from_attributes = True


class GenerateSummaryRequest(BaseModel):
    """Request schema for generating AI summary"""
    incident_id: str = Field(..., description="Incident ID to generate summary for")


class GenerateSummaryResponse(BaseModel):
    """Response schema for AI summary generation"""
    incident_id: str
    summary: str
    generated_at: str
    request_id: str
