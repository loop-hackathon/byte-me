"""
Cost anomaly detection service using PyOD and scikit-learn.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pyod.models.ecod import ECOD

from backend.models.cost import CostAggregate, CostAnomaly


def recompute_cost_anomalies(
    db: Session,
    user_id: int,
    min_history_days: int = 14,
    history_window_days: int = 60
) -> int:
    """
    Detect cost anomalies using PyOD ECOD algorithm.
    
    Args:
        db: Database session
        min_history_days: Minimum days of history required for detection
        history_window_days: Number of days to look back for training
        
    Returns:
        Number of anomalies detected
    """
    # Get latest date in aggregates for this user
    latest_date = db.query(func.max(CostAggregate.ts_date)).filter(CostAggregate.user_id == user_id).scalar()
    
    if not latest_date:
        return 0
    
    # Calculate date range
    start_date = latest_date - timedelta(days=history_window_days)
    
    # Get unique combinations of (team, service, env)
    combinations = db.query(
        CostAggregate.cloud,
        CostAggregate.team,
        CostAggregate.service,
        CostAggregate.env
    ).filter(CostAggregate.user_id == user_id).distinct().all()
    
    anomalies_detected = 0
    
    for cloud, team, service, env in combinations:
        # Query aggregates for this combination
        query = db.query(CostAggregate).filter(
            and_(
                CostAggregate.ts_date >= start_date,
                CostAggregate.ts_date <= latest_date,
                CostAggregate.cloud == cloud,
                CostAggregate.user_id == user_id
            )
        )
        
        if team:
            query = query.filter(CostAggregate.team == team)
        else:
            query = query.filter(CostAggregate.team.is_(None))
        
        if service:
            query = query.filter(CostAggregate.service == service)
        else:
            query = query.filter(CostAggregate.service.is_(None))
        
        if env:
            query = query.filter(CostAggregate.env == env)
        else:
            query = query.filter(CostAggregate.env.is_(None))
        
        aggregates = query.order_by(CostAggregate.ts_date).all()
        
        # Skip if insufficient data
        if len(aggregates) < min_history_days:
            continue
        
        # Convert to DataFrame
        data = []
        for agg in aggregates:
            data.append({
                'ts_date': agg.ts_date,
                'total_cost': float(agg.total_cost)
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('ts_date')
        
        # Add features
        df['rolling_mean_7'] = df['total_cost'].rolling(window=7, min_periods=1).mean()
        df['rolling_std_7'] = df['total_cost'].rolling(window=7, min_periods=1).std()
        df['day_of_week'] = pd.to_datetime(df['ts_date']).dt.dayofweek
        
        # Fill NaN values
        df['rolling_mean_7'] = df['rolling_mean_7'].fillna(df['total_cost'].mean())
        df['rolling_std_7'] = df['rolling_std_7'].fillna(0.0)
        
        # Build feature matrix
        X = np.column_stack([
            df['total_cost'].values,
            df['rolling_mean_7'].values,
            df['rolling_std_7'].values,
            df['day_of_week'].values
        ])
        
        # Skip if all costs are zero or constant
        if X[:, 0].std() == 0:
            continue
        
        # Train ECOD model on all but last 3 days
        train_size = max(min_history_days, len(X) - 3)
        X_train = X[:train_size]
        X_test = X[train_size:]
        
        if len(X_test) == 0:
            continue
        
        try:
            # Train anomaly detector
            clf = ECOD()
            clf.fit(X_train)
            
            # Score test data (last few days)
            scores = clf.decision_function(X_test)
            
            # Determine threshold (90th percentile of training scores)
            train_scores = clf.decision_function(X_train)
            threshold = np.percentile(train_scores, 90)
            
            # Identify anomalies
            test_indices = range(train_size, len(df))
            for idx, score in zip(test_indices, scores):
                if score > threshold:
                    row = df.iloc[idx]
                    actual_cost = row['total_cost']
                    expected_cost = row['rolling_mean_7']
                    
                    # Determine direction
                    if actual_cost > expected_cost:
                        direction = "spike"
                    else:
                        direction = "drop"
                    
                    # Determine severity based on deviation
                    if expected_cost > 0:
                        deviation_pct = abs(actual_cost - expected_cost) / expected_cost
                        if deviation_pct > 0.5:
                            severity = "high"
                        elif deviation_pct > 0.25:
                            severity = "medium"
                        else:
                            severity = "low"
                    else:
                        severity = "medium"
                    
                    # Check if anomaly already exists
                    existing = db.query(CostAnomaly).filter(
                        and_(
                            CostAnomaly.ts_date == row['ts_date'],
                            CostAnomaly.cloud == cloud,
                            CostAnomaly.team == team,
                            CostAnomaly.service == service,
                            CostAnomaly.env == env,
                            CostAnomaly.user_id == user_id
                        )
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.actual_cost = actual_cost
                        existing.expected_cost = expected_cost
                        existing.anomaly_score = float(score)
                        existing.direction = direction
                        existing.severity = severity
                    else:
                        # Insert new anomaly
                        anomaly = CostAnomaly(
                            ts_date=row['ts_date'],
                            cloud=cloud,
                            team=team,
                            service=service,
                            region=None,  # Not tracked at this aggregation level
                            env=env,
                            actual_cost=actual_cost,
                            expected_cost=expected_cost,
                            anomaly_score=float(score),
                            direction=direction,
                            severity=severity,
                            user_id=user_id
                        )
                        db.add(anomaly)
                    
                    anomalies_detected += 1
        
        except Exception as e:
            # Skip this combination if anomaly detection fails
            print(f"Anomaly detection failed for {cloud}/{team}/{service}/{env}: {e}")
            continue
    
    db.commit()
    return anomalies_detected
