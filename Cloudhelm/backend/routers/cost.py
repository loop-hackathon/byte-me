"""
Cost management API endpoints.
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional, List
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

from backend.core.db import get_db
from backend.core.config import settings
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.cost import CloudCost, CostAggregate, CostAnomaly, Budget
from backend.schemas.cost import (
    UploadResponse,
    RecomputeAggregatesRequest,
    RecomputeAggregatesResponse,
    CostSummaryResponse,
    CostSummarySeries,
    CostSummaryPoint,
    CostAnomalyResponse,
    BudgetStatusResponse,
    ForecastResponse,
    ForecastPoint
)
from backend.services.cost_ingestion import (
    ingest_aws_cost_csv,
    ingest_gcp_cost_file,
    ingest_azure_cost_csv
)
from backend.services.cost_aggregation import (
    recompute_cost_aggregates,
    get_budget_statuses
)
from backend.services.cost_anomaly import recompute_cost_anomalies
from backend.services.cost_billing import BillingService

router = APIRouter(prefix="/api/cost", tags=["cost"])


@router.post("/upload/aws", response_model=UploadResponse)
async def upload_aws_cost(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload AWS Cost and Usage Report (CUR) CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    return await ingest_aws_cost_csv(file, db, current_user.id)


@router.post("/upload/gcp", response_model=UploadResponse)
async def upload_gcp_cost(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload GCP billing export file (CSV or JSON)."""
    if not (file.filename.endswith('.csv') or file.filename.endswith('.json')):
        raise HTTPException(status_code=400, detail="File must be CSV or JSON")
    
    return await ingest_gcp_cost_file(file, db, current_user.id)


@router.post("/upload/azure", response_model=UploadResponse)
async def upload_azure_cost(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload Azure cost export CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    return await ingest_azure_cost_csv(file, db, current_user.id)


@router.post("/recompute-aggregates", response_model=RecomputeAggregatesResponse)
async def trigger_recompute_aggregates(
    body: RecomputeAggregatesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger recomputation of cost aggregates."""
    rows_upserted = recompute_cost_aggregates(db, current_user.id, body.start_date, body.end_date)
    
    # Get actual date range
    date_range = db.query(
        func.min(CostAggregate.ts_date).label('min_date'),
        func.max(CostAggregate.ts_date).label('max_date')
    ).filter(CostAggregate.user_id == current_user.id).first()
    
    return RecomputeAggregatesResponse(
        rows_upserted=rows_upserted,
        start_date=date_range.min_date or date.today(),
        end_date=date_range.max_date or date.today()
    )


@router.post("/recompute-anomalies")
async def trigger_recompute_anomalies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger recomputation of cost anomalies."""
    anomalies_detected = recompute_cost_anomalies(db, current_user.id)
    
    return {
        "anomalies_detected": anomalies_detected,
        "message": f"Detected {anomalies_detected} cost anomalies"
    }


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    group_by: str = Query("team", regex="^(team|service|cloud)$"),
    env: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cost summary grouped by specified dimension.
    
    Query parameters:
    - from: Start date (default: 30 days ago)
    - to: End date (default: today)
    - group_by: Grouping dimension (team, service, or cloud)
    - env: Filter by environment (optional)
    """
    # Default date range
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    # Build query
    query = db.query(CostAggregate).filter(
        and_(
            CostAggregate.ts_date >= from_date,
            CostAggregate.ts_date <= to_date,
            CostAggregate.user_id == current_user.id
        )
    )
    
    # Apply env filter
    if env:
        query = query.filter(CostAggregate.env == env)
    
    aggregates = query.all()
    
    # Group data
    series_data = {}
    for agg in aggregates:
        # Determine group key
        if group_by == "team":
            key = agg.team or "unassigned"
        elif group_by == "service":
            key = agg.service or "unknown"
        else:  # cloud
            key = agg.cloud
        
        if key not in series_data:
            series_data[key] = {}
        
        date_str = str(agg.ts_date)
        if date_str not in series_data[key]:
            series_data[key][date_str] = 0.0
        
        series_data[key][date_str] += float(agg.total_cost)
    
    # Convert to response format
    series = []
    total_cost = 0.0
    
    for key, dates in series_data.items():
        points = [
            CostSummaryPoint(date=date.fromisoformat(d), total_cost=cost)
            for d, cost in sorted(dates.items())
        ]
        series.append(CostSummarySeries(key=key, points=points))
        total_cost += sum(p.total_cost for p in points)
    
    return CostSummaryResponse(
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
        series=series,
        total_cost=total_cost
    )


@router.get("/anomalies", response_model=List[CostAnomalyResponse])
async def get_cost_anomalies(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    min_severity: str = Query("low", regex="^(low|medium|high)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detected cost anomalies.
    
    Query parameters:
    - from: Start date (default: 30 days ago)
    - to: End date (default: today)
    - min_severity: Minimum severity level (low, medium, high)
    """
    # Default date range
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    # Build query
    query = db.query(CostAnomaly).filter(
        and_(
            CostAnomaly.ts_date >= from_date,
            CostAnomaly.ts_date <= to_date,
            CostAnomaly.user_id == current_user.id
        )
    )
    
    # Apply severity filter
    severity_levels = {"low": 0, "medium": 1, "high": 2}
    min_level = severity_levels[min_severity]
    
    if min_level > 0:
        allowed_severities = [s for s, l in severity_levels.items() if l >= min_level]
        query = query.filter(CostAnomaly.severity.in_(allowed_severities))
    
    # Order by date desc, severity desc
    anomalies = query.order_by(
        desc(CostAnomaly.ts_date),
        desc(CostAnomaly.severity)
    ).all()
    
    return anomalies


@router.get("/budgets/status", response_model=List[BudgetStatusResponse])
async def get_budget_status(
    month: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get budget status for all budgets.
    
    Query parameters:
    - month: Month to calculate status for (default: current month)
    """
    return get_budget_statuses(db, current_user.id, month)


@router.get("/forecast", response_model=List[ForecastResponse])
async def get_cost_forecast(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cost forecast using linear regression.
    
    Query parameters:
    - days: Number of days to forecast (1-30, default: 7)
    """
    # Get last 180 days of data for training
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    # Query aggregates grouped by team
    aggregates = db.query(CostAggregate).filter(
        and_(
            CostAggregate.ts_date >= start_date,
            CostAggregate.ts_date <= end_date,
            CostAggregate.user_id == current_user.id
        )
    ).all()
    
    if len(aggregates) < 30:
        raise HTTPException(
            status_code=400,
            detail="Insufficient historical data for forecasting (minimum 30 days required)"
        )
    
    # Group by team
    team_data = {}
    for agg in aggregates:
        team = agg.team or "unassigned"
        if team not in team_data:
            team_data[team] = []
        team_data[team].append({
            'date': agg.ts_date,
            'cost': float(agg.total_cost)
        })
    
    # Generate forecasts for each team
    forecasts = []
    
    for team, data in team_data.items():
        if len(data) < 30:
            continue
        
        # Sort by date
        data = sorted(data, key=lambda x: x['date'])
        
        # Prepare data for linear regression
        dates = [d['date'] for d in data]
        costs = [d['cost'] for d in data]
        
        # Convert dates to numeric (days since first date)
        first_date = dates[0]
        X = np.array([(d - first_date).days for d in dates]).reshape(-1, 1)
        y = np.array(costs)
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate forecast
        last_date = dates[-1]
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        forecast_X = np.array([(d - first_date).days for d in forecast_dates]).reshape(-1, 1)
        forecast_y = model.predict(forecast_X)
        
        # Ensure non-negative forecasts
        forecast_y = np.maximum(forecast_y, 0)
        
        forecast_points = [
            ForecastPoint(date=d, projected_cost=float(c))
            for d, c in zip(forecast_dates, forecast_y)
        ]
        
        forecasts.append(ForecastResponse(
            key=team,
            forecast_points=forecast_points
        ))
    
    return forecasts


@router.post("/billing/analyze")
async def analyze_billing_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a cost CSV file using flexible column detection.
    Returns cost trends, anomalies, budget status, and AI insights.
    
    This endpoint processes the CSV entirely in-memory and returns
    immediate analysis results without storing to the database.
    Uses the BillingService from feature_2 for flexible parsing.
    """
    try:
        contents = await file.read()
        csv_content = contents.decode('utf-8', errors='replace')

        gemini_key = settings.gemini_api_key
        analysis = await BillingService.analyze(csv_content, gemini_key)

        # Convert to CloudHelm frontend format
        result = BillingService.convert_to_cloudhelm_format(
            analysis, current_user.id
        )

        return JSONResponse(content={
            "success": True,
            "data": analysis,
            "cloudhelm_format": result,
        })
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error analyzing CSV: {str(e)}"
        )


@router.post("/seed-demo")
async def seed_demo_cost_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Seed the database with demo cost data from the sample CSVs
    in the fetaures_2 directory. This populates the cost tables
    so the Cost Dashboard has data to display.
    Also auto-creates budgets and runs aggregation + anomaly detection.
    """
    try:
        # Locate sample CSV files
        base_dir = Path(__file__).parent.parent.parent  # project root
        csv_files = [
            base_dir / "fetaures_2" / "aws_unique_dates_sample.csv",
            base_dir / "fetaures_2" / "aws_cost_usage_sample_different.csv",
        ]

        total_rows = 0
        total_cost_amount = 0.0
        all_dates: list[date] = []

        for csv_path in csv_files:
            if not csv_path.exists():
                continue

            import pandas as pd, io
            df = pd.read_csv(str(csv_path))

            # Auto-detect columns
            cols = df.columns.tolist()
            service_col = next(
                (c for c in cols if 'service' in c.lower() or 'product' in c.lower()),
                cols[0]
            )
            cost_col = next(
                (c for c in cols if 'cost' in c.lower() or 'amount' in c.lower()),
                cols[-1]
            )
            date_col = next(
                (c for c in cols if 'date' in c.lower() or 'time' in c.lower()),
                None
            )
            region_col = next(
                (c for c in cols if 'zone' in c.lower() or 'region' in c.lower()
                 or 'availability' in c.lower()),
                None
            )
            usage_col = next(
                (c for c in cols if 'usage' in c.lower() and c != cost_col),
                None
            )
            currency_col = next(
                (c for c in cols if 'currency' in c.lower()),
                None
            )

            df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)

            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)

            for _, row in df.iterrows():
                try:
                    cost_val = float(row[cost_col])
                    if cost_val <= 0:
                        continue

                    if date_col and pd.notna(row[date_col]):
                        dt = row[date_col]
                        usage_date = dt.date() if hasattr(dt, 'date') else date.today()
                    else:
                        usage_date = date.today()

                    service = str(row[service_col])
                    region = str(row[region_col]) if region_col and pd.notna(row.get(region_col)) else 'us-east-1'
                    usage_type = str(row[usage_col]) if usage_col and pd.notna(row.get(usage_col)) else None
                    currency = str(row[currency_col]) if currency_col and pd.notna(row.get(currency_col)) else 'USD'

                    record = CloudCost(
                        ts_date=usage_date,
                        cloud='aws',
                        account_id='demo-account',
                        service=service,
                        region=region,
                        env='prod',
                        team=service.replace('Amazon', '').strip() + '-team',
                        usage_type=usage_type,
                        cost_amount=cost_val,
                        currency=currency,
                        user_id=current_user.id,
                    )
                    db.add(record)
                    total_rows += 1
                    total_cost_amount += cost_val
                    all_dates.append(usage_date)

                except (ValueError, TypeError):
                    continue

        db.commit()

        if total_rows == 0:
            raise HTTPException(
                status_code=400,
                detail="No sample CSV files found or no valid data in them."
            )

        # Auto-create budgets for each service/team
        service_costs = db.query(
            CloudCost.team,
            func.sum(CloudCost.cost_amount).label('total')
        ).filter(
            CloudCost.user_id == current_user.id
        ).group_by(CloudCost.team).all()

        import random
        for team_name, total in service_costs:
            if not team_name:
                continue
            existing = db.query(Budget).filter(
                Budget.team == team_name,
                Budget.user_id == current_user.id
            ).first()
            if not existing:
                variance = random.uniform(0.8, 1.3)
                budget = Budget(
                    team=team_name,
                    service=None,
                    monthly_budget_amount=float(total) * variance,
                    currency='USD',
                    user_id=current_user.id,
                )
                db.add(budget)

        db.commit()

        # Run aggregation
        min_date = min(all_dates) if all_dates else date.today()
        max_date = max(all_dates) if all_dates else date.today()
        agg_rows = recompute_cost_aggregates(
            db, current_user.id, min_date, max_date
        )

        # Run anomaly detection
        anomalies_detected = 0
        try:
            anomalies_detected = recompute_cost_anomalies(db, current_user.id)
        except Exception:
            pass  # Anomaly detection may fail with small datasets

        return {
            "success": True,
            "rows_ingested": total_rows,
            "total_cost": round(total_cost_amount, 2),
            "date_range": {
                "start": str(min_date),
                "end": str(max_date)
            },
            "aggregates_computed": agg_rows,
            "anomalies_detected": anomalies_detected,
            "message": f"Seeded {total_rows} cost records, computed {agg_rows} aggregates"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error seeding demo data: {str(e)}"
        )
