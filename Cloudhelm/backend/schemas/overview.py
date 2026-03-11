"""
Pydantic schemas for Overview Page API requests and responses.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


# KPI Summary Schemas
class SpendVsBudget(BaseModel):
    """Spend vs budget comparison."""
    percentage: float
    status: str  # "under", "at_risk", "over"


class KPIDeltas(BaseModel):
    """Delta values for KPIs compared to previous period."""
    spend_delta: str
    anomalies_delta: str
    incidents_delta: str
    deployments_delta: str


class KPISummaryResponse(BaseModel):
    """Response schema for KPI summary endpoint."""
    total_cloud_spend: float
    spend_vs_budget: SpendVsBudget
    forecasted_month_end: float
    active_anomalies: int
    potential_savings: float
    open_incidents: int
    availability: float
    error_rate: float
    deployments_count: int
    teams_at_risk: int
    deltas: KPIDeltas


# Cost Time Series Schemas
class CostTimeSeriesPoint(BaseModel):
    """Single point in cost time series."""
    date: str
    cost: float
    forecast: float
    anomaly: bool


class CostTimeSeriesResponse(BaseModel):
    """Response schema for cost time series endpoint."""
    series: List[CostTimeSeriesPoint]
    total_cost: float
    avg_daily_cost: float


# Spend Breakdown Schemas
class SpendByTeamItem(BaseModel):
    """Single team spend item."""
    team: str
    spend: float


class SpendByTeamResponse(BaseModel):
    """Response schema for spend by team endpoint."""
    breakdown: List[SpendByTeamItem]
    total_spend: float


class SpendByProviderItem(BaseModel):
    """Single provider spend item."""
    provider: str
    spend: float
    percentage: float
    color: str


class SpendByProviderResponse(BaseModel):
    """Response schema for spend by provider endpoint."""
    breakdown: List[SpendByProviderItem]
    total_spend: float


# Optimization Opportunities Schemas
class OptimizationOpportunity(BaseModel):
    """Single optimization opportunity."""
    resource: str
    estimated_savings: float
    type: str
    recommended_action: str
    service: str
    team: str


class OptimizationOpportunitiesResponse(BaseModel):
    """Response schema for optimization opportunities endpoint."""
    opportunities: List[OptimizationOpportunity]
    total_potential_savings: float


# Reliability Metrics Schemas
class IncidentItem(BaseModel):
    """Single incident item."""
    id: int
    title: str
    status: str
    severity: str
    duration: str
    service: Optional[str]
    team: Optional[str]


class MetricWithTrend(BaseModel):
    """Metric value with trend information."""
    percentage: float
    delta: str
    trend: str  # "positive" or "negative"


class MTTRMetrics(BaseModel):
    """Mean Time To Resolution metrics."""
    average: str
    median: str


class ReliabilityMetricsResponse(BaseModel):
    """Response schema for reliability metrics endpoint."""
    open_incidents: List[IncidentItem]
    availability: MetricWithTrend
    error_rate: MetricWithTrend
    mttr: MTTRMetrics


# Deployment Stats Schemas
class DeploymentItem(BaseModel):
    """Single deployment item."""
    id: int
    service: str
    environment: str
    status: str
    deployed_at: str
    deployed_by: Optional[str]
    version: Optional[str]


class DeploymentStatsResponse(BaseModel):
    """Response schema for deployment stats endpoint."""
    total_deployments: int
    successful: int
    failed: int
    delta: str
    recent_deployments: List[DeploymentItem]
