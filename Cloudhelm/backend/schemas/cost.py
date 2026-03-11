"""
Pydantic schemas for Cost-related API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal


class UploadResponse(BaseModel):
    """Response schema for cost file upload."""
    rows_ingested: int
    start_date: date
    end_date: date
    total_cost: float
    cloud: str


class RecomputeAggregatesRequest(BaseModel):
    """Request schema for recomputing aggregates."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class RecomputeAggregatesResponse(BaseModel):
    """Response schema for recompute aggregates."""
    rows_upserted: int
    start_date: date
    end_date: date


class CostSummaryPoint(BaseModel):
    """Single data point in cost summary time series."""
    date: date
    total_cost: float


class CostSummarySeries(BaseModel):
    """Time series for a single group (team/service/cloud)."""
    key: str
    points: List[CostSummaryPoint]


class CostSummaryResponse(BaseModel):
    """Response schema for cost summary API."""
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    group_by: str
    series: List[CostSummarySeries]
    total_cost: float
    
    class Config:
        populate_by_name = True


class CostAnomalyResponse(BaseModel):
    """Response schema for a single cost anomaly."""
    id: int
    ts_date: date
    cloud: str
    team: Optional[str]
    service: Optional[str]
    region: Optional[str]
    env: Optional[str]
    actual_cost: float
    expected_cost: float
    anomaly_score: float
    direction: str
    severity: str
    
    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    """Response schema for budget status."""
    team: str
    service: Optional[str]
    monthly_budget: float
    mtd_cost: float
    projected_cost: float
    status: str  # "UNDER", "AT_RISK", "OVER"
    currency: str


class ForecastPoint(BaseModel):
    """Single forecast data point."""
    date: date
    projected_cost: float


class ForecastResponse(BaseModel):
    """Response schema for cost forecast."""
    key: str  # team or service name
    forecast_points: List[ForecastPoint]
