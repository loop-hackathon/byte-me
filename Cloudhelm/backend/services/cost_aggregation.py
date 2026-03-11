"""
Cost aggregation and budget status services.
"""
import pandas as pd
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from calendar import monthrange

from backend.models.cost import CloudCost, CostAggregate, Budget
from backend.schemas.cost import BudgetStatusResponse


def recompute_cost_aggregates(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    Recompute cost aggregates for the given date range.
    
    Args:
        db: Database session
        start_date: Start date (inclusive), defaults to min date in CloudCost
        end_date: End date (inclusive), defaults to max date in CloudCost
        
    Returns:
        Number of aggregate rows upserted
    """
    # Determine date range if not provided
    if not start_date or not end_date:
        date_range = db.query(
            func.min(CloudCost.ts_date).label('min_date'),
            func.max(CloudCost.ts_date).label('max_date')
        ).filter(CloudCost.user_id == user_id).first()
        
        if not date_range.min_date:
            return 0  # No data to aggregate
        
        start_date = start_date or date_range.min_date
        end_date = end_date or date_range.max_date
    
    # Query CloudCost for date range
    costs = db.query(CloudCost).filter(
        and_(
            CloudCost.ts_date >= start_date,
            CloudCost.ts_date <= end_date,
            CloudCost.user_id == user_id
        )
    ).all()
    
    if not costs:
        return 0
    
    # Convert to DataFrame for easier aggregation
    data = []
    for cost in costs:
        data.append({
            'ts_date': cost.ts_date,
            'cloud': cost.cloud,
            'team': cost.team or '*',
            'service': cost.service or '*',
            'region': cost.region or '*',
            'env': cost.env or '*',
            'cost_amount': float(cost.cost_amount)
        })
    
    df = pd.DataFrame(data)
    
    # Group by dimensions and sum costs
    grouped = df.groupby([
        'ts_date', 'cloud', 'team', 'service', 'region', 'env'
    ])['cost_amount'].sum().reset_index()
    
    # Upsert aggregates
    rows_upserted = 0
    for _, row in grouped.iterrows():
        # Check if aggregate exists
        existing = db.query(CostAggregate).filter(
            and_(
                CostAggregate.ts_date == row['ts_date'],
                CostAggregate.cloud == row['cloud'],
                CostAggregate.team == (None if row['team'] == '*' else row['team']),
                CostAggregate.service == (None if row['service'] == '*' else row['service']),
                CostAggregate.region == (None if row['region'] == '*' else row['region']),
                CostAggregate.env == (None if row['env'] == '*' else row['env']),
                CostAggregate.user_id == user_id
            )
        ).first()
        
        if existing:
            # Update existing
            existing.total_cost = row['cost_amount']
        else:
            # Insert new
            aggregate = CostAggregate(
                ts_date=row['ts_date'],
                cloud=row['cloud'],
                team=None if row['team'] == '*' else row['team'],
                service=None if row['service'] == '*' else row['service'],
                region=None if row['region'] == '*' else row['region'],
                env=None if row['env'] == '*' else row['env'],
                total_cost=row['cost_amount'],
                user_id=user_id
            )
            db.add(aggregate)
        
        rows_upserted += 1
    
    db.commit()
    return rows_upserted


def get_budget_statuses(db: Session, user_id: int, month: Optional[date] = None) -> List[BudgetStatusResponse]:
    """
    Calculate budget status for all budgets in the given month.
    
    Args:
        db: Database session
        month: Month to calculate status for (defaults to current month)
        
    Returns:
        List of budget status responses
    """
    if not month:
        month = date.today()
    
    # Get start and end of month
    month_start = date(month.year, month.month, 1)
    days_in_month = monthrange(month.year, month.month)[1]
    month_end = date(month.year, month.month, days_in_month)
    
    # Get current day for MTD calculation
    today = date.today()
    if today.year == month.year and today.month == month.month:
        current_day = today
    else:
        current_day = month_end
    
    days_passed = current_day.day
    
    # Get all budgets for user
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    
    results = []
    for budget in budgets:
        # Query aggregates for this budget
        query = db.query(func.sum(CostAggregate.total_cost)).filter(
            and_(
                CostAggregate.ts_date >= month_start,
                CostAggregate.ts_date <= current_day,
                CostAggregate.team == budget.team,
                CostAggregate.user_id == user_id
            )
        )
        
        # Add service filter if budget is service-specific
        if budget.service:
            query = query.filter(CostAggregate.service == budget.service)
        
        mtd_cost = query.scalar() or 0.0
        
        # Calculate projected cost
        if days_passed > 0:
            projected_cost = (float(mtd_cost) / days_passed) * days_in_month
        else:
            projected_cost = 0.0
        
        # Determine status
        budget_amount = float(budget.monthly_budget_amount)
        if projected_cost < 0.9 * budget_amount:
            status = "UNDER"
        elif projected_cost <= 1.1 * budget_amount:
            status = "AT_RISK"
        else:
            status = "OVER"
        
        results.append(BudgetStatusResponse(
            team=budget.team,
            service=budget.service,
            monthly_budget=budget_amount,
            mtd_cost=float(mtd_cost),
            projected_cost=projected_cost,
            status=status,
            currency=budget.currency
        ))
    
    return results
