"""
Overview Page API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, case
from typing import Optional, List
from datetime import date, timedelta, datetime
from decimal import Decimal

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.cost import CostAggregate, CostAnomaly, Budget, Incident, Deployment
from backend.schemas.overview import (
    KPISummaryResponse,
    SpendVsBudget,
    KPIDeltas,
    CostTimeSeriesResponse,
    CostTimeSeriesPoint,
    SpendByTeamResponse,
    SpendByTeamItem,
    SpendByProviderResponse,
    SpendByProviderItem,
    OptimizationOpportunitiesResponse,
    OptimizationOpportunity,
    ReliabilityMetricsResponse,
    IncidentItem,
    MetricWithTrend,
    MTTRMetrics,
    DeploymentStatsResponse,
    DeploymentItem
)

router = APIRouter(prefix="/api/overview", tags=["overview"])


def parse_time_range(time_range: str) -> tuple[date, date]:
    """Parse time range string to start and end dates."""
    today = date.today()
    if time_range == "7d":
        start_date = today - timedelta(days=7)
    elif time_range == "30d":
        start_date = today - timedelta(days=30)
    elif time_range == "90d":
        start_date = today - timedelta(days=90)
    else:
        start_date = today - timedelta(days=30)  # default
    
    return start_date, today


@router.get("/kpi-summary", response_model=KPISummaryResponse)
async def get_kpi_summary(
    time_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    environment: str = Query("all", regex="^(all|prod|staging|dev)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get aggregated KPI metrics for the overview page - OPTIMIZED."""
    start_date, end_date = parse_time_range(time_range)
    
    # Build environment filter
    env_filter = []
    if environment != "all":
        env_filter.append(CostAggregate.env == environment)
    
    # OPTIMIZATION: Single query for all cost metrics
    month_start = date.today().replace(day=1)
    seven_days_ago = date.today() - timedelta(days=7)
    
    cost_metrics = db.query(
        func.sum(case((
            and_(CostAggregate.ts_date >= start_date, CostAggregate.ts_date <= end_date),
            CostAggregate.total_cost
        ), else_=0)).label('total_spend'),
        func.sum(case((
            and_(CostAggregate.ts_date >= month_start, CostAggregate.ts_date <= date.today()),
            CostAggregate.total_cost
        ), else_=0)).label('mtd_spend')
    ).filter(*env_filter).first()
    
    total_spend = float(cost_metrics.total_spend or 0)
    mtd_spend = float(cost_metrics.mtd_spend or 0)
    
    # OPTIMIZATION: Single query for anomalies and incidents
    counts = db.query(
        func.count(CostAnomaly.id).label('anomalies'),
        func.count(Incident.id).label('incidents'),
        func.count(Deployment.id).label('deployments')
    ).select_from(CostAnomaly).outerjoin(
        Incident, Incident.status.in_(["open", "investigating"])
    ).outerjoin(
        Deployment, Deployment.deployed_at >= seven_days_ago
    ).filter(
        and_(
            CostAnomaly.ts_date >= start_date,
            CostAnomaly.ts_date <= end_date,
            *([CostAnomaly.env == environment] if environment != "all" else [])
        )
    ).first()
    
    active_anomalies = counts.anomalies if counts else 0
    open_incidents = counts.incidents if counts else 0
    deployments_count = counts.deployments if counts else 0
    
    # Budget calculation
    budget_query = db.query(Budget).first()
    if budget_query:
        monthly_budget = float(budget_query.monthly_budget_amount)
        days_in_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        days_passed = (date.today() - month_start).days + 1
        projected = mtd_spend / days_passed * days_in_month.day if days_passed > 0 else 0
        
        budget_percentage = ((projected - monthly_budget) / monthly_budget * 100) if monthly_budget > 0 else 0
        
        if projected > monthly_budget * 1.1:
            budget_status = "over"
        elif projected > monthly_budget * 0.9:
            budget_status = "at_risk"
        else:
            budget_status = "under"
        
        spend_vs_budget = SpendVsBudget(percentage=budget_percentage, status=budget_status)
        forecasted_month_end = projected
    else:
        spend_vs_budget = SpendVsBudget(percentage=0, status="under")
        forecasted_month_end = 0
    
    # Mock data for fields without DB tables yet
    potential_savings = 27500.0
    availability = 99.94
    error_rate = 0.08
    teams_at_risk = 3
    
    deltas = KPIDeltas(
        spend_delta="+12.5%",
        anomalies_delta="-2",
        incidents_delta="-1",
        deployments_delta="+6"
    )
    
    return KPISummaryResponse(
        total_cloud_spend=total_spend,
        spend_vs_budget=spend_vs_budget,
        forecasted_month_end=forecasted_month_end,
        active_anomalies=active_anomalies,
        potential_savings=potential_savings,
        open_incidents=open_incidents,
        availability=availability,
        error_rate=error_rate,
        deployments_count=deployments_count,
        teams_at_risk=teams_at_risk,
        deltas=deltas
    )


@router.get("/cost-timeseries", response_model=CostTimeSeriesResponse)
async def get_cost_timeseries(
    time_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    environment: str = Query("all", regex="^(all|prod|staging|dev)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily cost time series with forecast and anomaly markers - OPTIMIZED."""
    start_date, end_date = parse_time_range(time_range)
    
    # Build environment filter
    env_filter = []
    if environment != "all":
        env_filter.append(CostAggregate.env == environment)
    
    # OPTIMIZATION: Single query with subquery for anomalies
    daily_costs_query = db.query(
        CostAggregate.ts_date,
        func.sum(CostAggregate.total_cost).label('total'),
        func.bool_or(CostAnomaly.id.isnot(None)).label('has_anomaly')
    ).outerjoin(
        CostAnomaly,
        and_(
            CostAnomaly.ts_date == CostAggregate.ts_date,
            *([CostAnomaly.env == environment] if environment != "all" else [])
        )
    ).filter(
        and_(
            CostAggregate.ts_date >= start_date,
            CostAggregate.ts_date <= end_date,
            *env_filter
        )
    ).group_by(CostAggregate.ts_date).order_by(CostAggregate.ts_date)
    
    daily_costs = daily_costs_query.all()
    
    # Build series with simple forecast (moving average)
    series = []
    costs = [float(row.total) for row in daily_costs]
    
    for i, row in enumerate(daily_costs):
        # Simple forecast: 7-day moving average
        if i >= 6:
            forecast = sum(costs[i-6:i+1]) / 7
        else:
            forecast = costs[i] if costs else 0
        
        series.append(CostTimeSeriesPoint(
            date=row.ts_date.isoformat(),
            cost=float(row.total),
            forecast=forecast,
            anomaly=bool(row.has_anomaly)
        ))
    
    total_cost = sum(costs)
    avg_daily_cost = total_cost / len(costs) if costs else 0
    
    return CostTimeSeriesResponse(
        series=series,
        total_cost=total_cost,
        avg_daily_cost=avg_daily_cost
    )


@router.get("/spend-by-team", response_model=SpendByTeamResponse)
async def get_spend_by_team(
    time_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    environment: str = Query("all", regex="^(all|prod|staging|dev)$"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spend breakdown by team."""
    start_date, end_date = parse_time_range(time_range)
    
    # Build environment filter
    env_filter = []
    if environment != "all":
        env_filter.append(CostAggregate.env == environment)
    
    # Query spend by team
    team_spend = db.query(
        CostAggregate.team,
        func.sum(CostAggregate.total_cost).label('spend')
    ).filter(
        and_(
            CostAggregate.ts_date >= start_date,
            CostAggregate.ts_date <= end_date,
            CostAggregate.team.isnot(None),
            *env_filter
        )
    ).group_by(CostAggregate.team).order_by(desc('spend')).limit(limit).all()
    
    breakdown = [
        SpendByTeamItem(team=row.team, spend=float(row.spend))
        for row in team_spend
    ]
    
    total_spend = sum(item.spend for item in breakdown)
    
    return SpendByTeamResponse(
        breakdown=breakdown,
        total_spend=total_spend
    )


@router.get("/spend-by-provider", response_model=SpendByProviderResponse)
async def get_spend_by_provider(
    time_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    environment: str = Query("all", regex="^(all|prod|staging|dev)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spend breakdown by cloud provider."""
    start_date, end_date = parse_time_range(time_range)
    
    # Build environment filter
    env_filter = []
    if environment != "all":
        env_filter.append(CostAggregate.env == environment)
    
    # Query spend by provider
    provider_spend = db.query(
        CostAggregate.cloud,
        func.sum(CostAggregate.total_cost).label('spend')
    ).filter(
        and_(
            CostAggregate.ts_date >= start_date,
            CostAggregate.ts_date <= end_date,
            *env_filter
        )
    ).group_by(CostAggregate.cloud).order_by(desc('spend')).all()
    
    # Provider colors
    colors = {
        "aws": "#FF9900",
        "azure": "#0078D4",
        "gcp": "#4285F4"
    }
    
    total_spend = sum(float(row.spend) for row in provider_spend)
    
    breakdown = [
        SpendByProviderItem(
            provider=row.cloud.upper(),
            spend=float(row.spend),
            percentage=round((float(row.spend) / total_spend * 100) if total_spend > 0 else 0, 1),
            color=colors.get(row.cloud.lower(), "#999999")
        )
        for row in provider_spend
    ]
    
    return SpendByProviderResponse(
        breakdown=breakdown,
        total_spend=total_spend
    )


@router.get("/optimization-opportunities", response_model=OptimizationOpportunitiesResponse)
async def get_optimization_opportunities(
    limit: int = Query(4, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top optimization opportunities (mock data for now)."""
    # TODO: Implement real optimization detection logic
    opportunities = [
        OptimizationOpportunity(
            resource="EC2 i3.8xlarge (3 instances)",
            estimated_savings=12400.0,
            type="Over-provisioned",
            recommended_action="Downsize to i3.4xlarge",
            service="EC2",
            team="Engineering"
        ),
        OptimizationOpportunity(
            resource="RDS db.r5.4xlarge",
            estimated_savings=8200.0,
            type="Idle",
            recommended_action="Stop or delete unused DB",
            service="RDS",
            team="Data Science"
        ),
        OptimizationOpportunity(
            resource="S3 Glacier Storage",
            estimated_savings=4800.0,
            type="Unused",
            recommended_action="Delete old backups",
            service="S3",
            team="DevOps"
        ),
        OptimizationOpportunity(
            resource="EBS Volumes (unattached)",
            estimated_savings=2100.0,
            type="Idle",
            recommended_action="Delete unattached volumes",
            service="EBS",
            team="Engineering"
        )
    ]
    
    opportunities = opportunities[:limit]
    total_savings = sum(opp.estimated_savings for opp in opportunities)
    
    return OptimizationOpportunitiesResponse(
        opportunities=opportunities,
        total_potential_savings=total_savings
    )


@router.get("/reliability-metrics", response_model=ReliabilityMetricsResponse)
async def get_reliability_metrics(
    time_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reliability metrics including incidents, availability, and error rate."""
    start_date, end_date = parse_time_range(time_range)
    
    # Get open incidents
    incidents = db.query(Incident).filter(
        Incident.status.in_(["open", "investigating"])
    ).order_by(desc(Incident.created_at)).limit(10).all()
    
    incident_items = []
    for incident in incidents:
        # Calculate duration
        duration_days = (date.today() - incident.created_at).days
        if duration_days == 0:
            duration = f"{(datetime.now() - datetime.combine(incident.created_at, datetime.min.time())).seconds // 3600}h"
        else:
            duration = f"{duration_days}d"
        
        incident_items.append(IncidentItem(
            id=incident.id,
            title=incident.title,
            status=incident.status,
            severity=incident.severity,
            duration=duration,
            service=incident.service,
            team=incident.team
        ))
    
    # Mock availability and error rate data
    availability = MetricWithTrend(
        percentage=99.94,
        delta="+0.02%",
        trend="positive"
    )
    
    error_rate = MetricWithTrend(
        percentage=0.08,
        delta="-0.03%",
        trend="positive"
    )
    
    mttr = MTTRMetrics(
        average="45m",
        median="30m"
    )
    
    return ReliabilityMetricsResponse(
        open_incidents=incident_items,
        availability=availability,
        error_rate=error_rate,
        mttr=mttr
    )


@router.get("/deployment-stats", response_model=DeploymentStatsResponse)
async def get_deployment_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get deployment statistics for the last 7 days."""
    seven_days_ago = date.today() - timedelta(days=7)
    
    # Get deployments
    deployments = db.query(Deployment).filter(
        Deployment.deployed_at >= seven_days_ago
    ).order_by(desc(Deployment.deployed_at)).all()
    
    total = len(deployments)
    successful = sum(1 for d in deployments if d.status == "success")
    failed = sum(1 for d in deployments if d.status == "failed")
    
    # Get previous period for delta
    fourteen_days_ago = date.today() - timedelta(days=14)
    prev_deployments = db.query(func.count(Deployment.id)).filter(
        and_(
            Deployment.deployed_at >= fourteen_days_ago,
            Deployment.deployed_at < seven_days_ago
        )
    ).scalar() or 0
    
    delta = f"+{total - prev_deployments}" if total >= prev_deployments else f"{total - prev_deployments}"
    
    # Get recent deployments
    recent = deployments[:5]
    recent_items = [
        DeploymentItem(
            id=d.id,
            service=d.service,
            environment=d.environment,
            status=d.status,
            deployed_at=d.deployed_at.isoformat(),
            deployed_by=d.deployed_by,
            version=d.version
        )
        for d in recent
    ]
    
    return DeploymentStatsResponse(
        total_deployments=total,
        successful=successful,
        failed=failed,
        delta=delta,
        recent_deployments=recent_items
    )
