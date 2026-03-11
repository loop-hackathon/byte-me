"""
Cost-related models for cloud cost tracking and analysis.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Float, Index, ForeignKey
import sqlalchemy as sa
from backend.core.db import Base


class CloudCost(Base):
    """Raw cost data ingested from cloud provider exports."""
    
    __tablename__ = "cloud_cost"
    
    id = Column(Integer, primary_key=True, index=True)
    ts_date = Column(Date, nullable=False, index=True)
    cloud = Column(String, nullable=False, index=True)  # "aws", "gcp", "azure"
    account_id = Column(String, nullable=False)
    service = Column(String, nullable=False, index=True)
    region = Column(String, nullable=False)
    env = Column(String, nullable=True)  # "prod", "stage", "dev"
    team = Column(String, nullable=True)
    usage_type = Column(String, nullable=True)
    cost_amount = Column(Numeric(18, 6), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_cloud_cost_date_cloud_service', 'ts_date', 'cloud', 'service'),
    )
    
    def __repr__(self):
        return f"<CloudCost(date={self.ts_date}, cloud={self.cloud}, service={self.service}, cost={self.cost_amount})>"


class CostAggregate(Base):
    """Pre-computed cost aggregations for fast querying."""
    
    __tablename__ = "cost_agg"
    
    id = Column(Integer, primary_key=True, index=True)
    ts_date = Column(Date, nullable=False, index=True)
    cloud = Column(String, nullable=False, index=True)
    team = Column(String, nullable=True)
    service = Column(String, nullable=True)
    region = Column(String, nullable=True)
    env = Column(String, nullable=True)
    total_cost = Column(Numeric(18, 6), nullable=False)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    __table_args__ = (
        Index(
            'idx_cost_agg_unique',
            'ts_date', 'cloud',
            'team', 'service', 'region', 'env',
            unique=True,
            postgresql_where=None
        ),
        Index('idx_cost_agg_date_cloud_team', 'ts_date', 'cloud', 'team'),
    )
    
    def __repr__(self):
        return f"<CostAggregate(date={self.ts_date}, cloud={self.cloud}, team={self.team}, cost={self.total_cost})>"


class Budget(Base):
    """Monthly budget definitions for cost tracking."""
    
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    team = Column(String, nullable=False, index=True)
    service = Column(String, nullable=True)  # Null means team-wide budget
    monthly_budget_amount = Column(Numeric(18, 6), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    def __repr__(self):
        return f"<Budget(team={self.team}, service={self.service}, budget={self.monthly_budget_amount})>"


class CostAnomaly(Base):
    """Detected cost anomalies from ML analysis."""
    
    __tablename__ = "cost_anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    ts_date = Column(Date, nullable=False, index=True)
    cloud = Column(String, nullable=False)
    team = Column(String, nullable=True)
    service = Column(String, nullable=True)
    region = Column(String, nullable=True)
    env = Column(String, nullable=True)
    actual_cost = Column(Numeric(18, 6), nullable=False)
    expected_cost = Column(Numeric(18, 6), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    direction = Column(String, nullable=False)  # "spike" or "drop"
    severity = Column(String, nullable=False)  # "low", "medium", "high"
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_cost_anomaly_date_severity', 'ts_date', 'severity'),
    )
    
    def __repr__(self):
        return f"<CostAnomaly(date={self.ts_date}, cloud={self.cloud}, severity={self.severity}, direction={self.direction})>"


class Incident(Base):
    """Incident tracking for reliability monitoring with AI-powered summaries."""
    
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "INC-2024-001"
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)  # Text field for description
    status = Column(String(50), nullable=False, index=True)  # "investigating", "identified", "monitoring", "resolved"
    severity = Column(String(50), nullable=False, index=True)  # "low", "medium", "high", "critical"
    created_at = Column(Date, nullable=False, index=True)
    resolved_at = Column(Date, nullable=True)
    service = Column(String(100), nullable=True, index=True)
    team = Column(String(100), nullable=True)
    env = Column(String(50), nullable=True)  # "prod", "staging", "dev"
    
    # AI Summary fields (from T-HACK integration)
    anomalies = Column(String, nullable=True)  # Text description of anomalies
    recent_releases = Column(String, nullable=True)  # Text description of recent releases
    metrics_summary = Column(String, nullable=True)  # Text summary of metrics
    cost_changes = Column(String, nullable=True)  # Text description of cost impact
    ai_summary = Column(String, nullable=True)  # AI-generated markdown summary
    summary_generated_at = Column(Date, nullable=True)
    
    __table_args__ = (
        Index('idx_incident_status_created', 'status', 'created_at'),
        Index('idx_incident_service_env', 'service', 'env'),
    )
    
    def __repr__(self):
        return f"<Incident(id={self.id}, incident_id={self.incident_id}, title={self.title}, status={self.status}, severity={self.severity})>"


class Deployment(Base):
    """Deployment tracking for release monitoring."""
    
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), nullable=False, index=True)
    environment = Column(String(50), nullable=False)  # "prod", "staging", "dev"
    status = Column(String(50), nullable=False, index=True)  # "success", "failed", "in_progress"
    deployed_at = Column(Date, nullable=False, index=True)
    deployed_by = Column(String(100), nullable=True)
    version = Column(String(100), nullable=True)
    commit_sha = Column(String(100), nullable=True)
    user_id = Column(Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_deployment_deployed_at_status', 'deployed_at', 'status'),
        Index('idx_deployment_service_env', 'service', 'environment'),
    )
    
    def __repr__(self):
        return f"<Deployment(id={self.id}, service={self.service}, env={self.environment}, status={self.status})>"
