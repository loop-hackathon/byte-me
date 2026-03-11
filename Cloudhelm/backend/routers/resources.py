"""
Resource efficiency router for CloudHelm.
Adapted from Loop_ResourceDashboard.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
import logging

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.resource import Resource, ResourceMetric, Recommendation
from backend.services.resource_analysis import (
    analyze_resource_utilization,
    generate_rightsizing_recommendation,
    generate_schedule_recommendation,
    calculate_average_metrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])


# Pydantic Schemas
class MetricIngest(BaseModel):
    """Schema for ingesting resource metrics."""
    resource_id: str = Field(..., description="Resource ID")
    resource_name: Optional[str] = Field(None, description="Resource name (auto-creates if not exists)")
    resource_type: Optional[str] = Field("vm", description="Resource type")
    team: Optional[str] = Field("default", description="Team name")
    environment: Optional[str] = Field("production", description="Environment")
    cpu_utilization: float = Field(..., ge=0, le=100, description="CPU utilization percentage")
    memory_utilization: float = Field(..., ge=0, le=100, description="Memory utilization percentage")
    disk_io: Optional[float] = Field(None, ge=0, description="Disk I/O in MB/s")
    network_io: Optional[float] = Field(None, ge=0, description="Network I/O in MB/s")
    timestamp: Optional[datetime] = None
    
    @validator('cpu_utilization', 'memory_utilization')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Utilization must be between 0 and 100')
        return v


class ResourceResponse(BaseModel):
    """Schema for resource response."""
    id: str
    name: str
    resource_type: str
    team: str
    environment: str
    waste_score: float
    avg_cpu: Optional[float] = None
    avg_memory: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    id: int
    resource_id: str
    resource_name: Optional[str] = None
    recommendation_type: str
    description: str
    potential_savings: float
    suggested_action: str
    confidence: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    average_waste_score: float
    underutilized_vms: int
    potential_savings: float
    schedulable_resources: int


# Endpoints

@router.post("/ingest")
def ingest_metrics(
    metric: MetricIngest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest resource metrics and trigger analysis.
    
    Auto-creates resource if it doesn't exist.
    """
    try:
        # Check if resource exists, create if not
        resource = db.query(Resource).filter(
            Resource.id == metric.resource_id,
            Resource.user_id == current_user.id
        ).first()
        
        if not resource:
            # Auto-create resource
            resource = Resource(
                id=metric.resource_id,
                name=metric.resource_name or metric.resource_id,
                resource_type=metric.resource_type,
                team=metric.team,
                environment=metric.environment,
                user_id=current_user.id
            )
            db.add(resource)
            db.commit()
            db.refresh(resource)
            logger.info(f"Auto-created resource: {resource.name}")
        
        # Save metric
        new_metric = ResourceMetric(
            resource_id=metric.resource_id,
            timestamp=metric.timestamp or datetime.utcnow(),
            cpu_utilization=metric.cpu_utilization,
            memory_utilization=metric.memory_utilization,
            disk_io=metric.disk_io,
            network_io=metric.network_io
        )
        db.add(new_metric)
        db.commit()
        
        # Trigger analysis
        analyze_resource_utilization(db, metric.resource_id, current_user.id)
        generate_rightsizing_recommendation(db, metric.resource_id, current_user.id)
        generate_schedule_recommendation(db, metric.resource_id, current_user.id)
        
        return {
            "status": "ingested",
            "resource_id": metric.resource_id,
            "resource_name": resource.name
        }
        
    except Exception as e:
        logger.error(f"Error ingesting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    team: Optional[str] = Query(None, description="Filter by team"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics - SUPER OPTIMIZED with single query.
    
    Returns average waste score, underutilized VM count, potential savings, and schedulable resources.
    """
    try:
        # Build filters
        filters = []
        if team:
            filters.append(Resource.team == team)
        if environment:
            filters.append(Resource.environment == environment)
        filters.append(Resource.user_id == current_user.id)
        
        # OPTIMIZATION: Single mega-query for all stats
        stats = db.query(
            func.avg(Resource.waste_score).label('avg_waste'),
            func.count(Resource.id).label('total_count'),
            func.sum(case((Resource.waste_score > 30, 1), else_=0)).label('underutilized'),
            func.coalesce(func.sum(Recommendation.potential_savings), 0).label('total_savings'),
            func.sum(case((Recommendation.recommendation_type == "schedule", 1), else_=0)).label('schedulable')
        ).outerjoin(Recommendation, Resource.id == Recommendation.resource_id)
        
        if filters:
            stats = stats.filter(and_(*filters))
        
        result = stats.first()
        
        if not result or result.total_count == 0:
            return DashboardStats(
                average_waste_score=0.0,
                underutilized_vms=0,
                potential_savings=0.0,
                schedulable_resources=0
            )
        
        return DashboardStats(
            average_waste_score=round(float(result.avg_waste or 0), 2),
            underutilized_vms=int(result.underutilized or 0),
            potential_savings=round(float(result.total_savings or 0), 2),
            schedulable_resources=int(result.schedulable or 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ResourceResponse])
def list_resources(
    team: Optional[str] = Query(None, description="Filter by team"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    search: Optional[str] = Query(None, description="Search by name"),
    min_waste_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum waste score"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all resources with optional filtering - OPTIMIZED with single query.
    
    Includes average CPU and memory utilization from recent metrics.
    """
    try:
        # OPTIMIZATION: Single query with subquery for metrics
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Subquery for average metrics
        metrics_subq = db.query(
            ResourceMetric.resource_id,
            func.avg(ResourceMetric.cpu_utilization).label('avg_cpu'),
            func.avg(ResourceMetric.memory_utilization).label('avg_memory')
        ).filter(
            ResourceMetric.timestamp >= seven_days_ago
        ).group_by(ResourceMetric.resource_id).subquery()
        
        # Main query with left join to metrics
        query = db.query(
            Resource,
            metrics_subq.c.avg_cpu,
            metrics_subq.c.avg_memory
        ).outerjoin(
            metrics_subq,
            Resource.id == metrics_subq.c.resource_id
        ).filter(Resource.user_id == current_user.id)
        
        # Apply filters
        if team:
            query = query.filter(Resource.team == team)
        if environment:
            query = query.filter(Resource.environment == environment)
        if search:
            query = query.filter(Resource.name.ilike(f"%{search}%"))
        if min_waste_score is not None:
            query = query.filter(Resource.waste_score >= min_waste_score)
        
        # Execute query
        results = query.order_by(Resource.waste_score.desc()).all()
        
        # Build response
        return [
            ResourceResponse(
                id=resource.id,
                name=resource.name,
                resource_type=resource.resource_type,
                team=resource.team,
                environment=resource.environment,
                waste_score=resource.waste_score,
                avg_cpu=float(avg_cpu) if avg_cpu else None,
                avg_memory=float(avg_memory) if avg_memory else None,
                created_at=resource.created_at
            )
            for resource, avg_cpu, avg_memory in results
        ]
        
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    recommendation_type: Optional[str] = Query(None, description="Filter by type (rightsizing, schedule)"),
    team: Optional[str] = Query(None, description="Filter by team"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all recommendations with optional filtering - OPTIMIZED with single query.
    
    Includes resource name for display.
    """
    try:
        # OPTIMIZATION: Single query with join to get resource names
        query = db.query(
            Recommendation,
            Resource.name.label('resource_name')
        ).join(Resource, Recommendation.resource_id == Resource.id).filter(
            Recommendation.user_id == current_user.id,
            Resource.user_id == current_user.id
        )
        
        # Apply filters
        if recommendation_type:
            query = query.filter(Recommendation.recommendation_type == recommendation_type)
        if team:
            query = query.filter(Resource.team == team)
        if environment:
            query = query.filter(Resource.environment == environment)
        
        # Execute query
        results = query.order_by(Recommendation.potential_savings.desc()).all()
        
        # Build response
        return [
            RecommendationResponse(
                id=rec.id,
                resource_id=rec.resource_id,
                resource_name=resource_name,
                recommendation_type=rec.recommendation_type,
                description=rec.description,
                potential_savings=rec.potential_savings,
                suggested_action=rec.suggested_action,
                confidence=rec.confidence,
                created_at=rec.created_at
            )
            for rec, resource_name in results
        ]
        
    except Exception as e:
        logger.error(f"Error listing recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed")
def seed_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Seed database with comprehensive demo data for testing.
    
    Creates realistic resources, metrics, and recommendations across multiple teams and environments.
    """
    try:
        # Clear existing data for user
        db.query(ResourceMetric).filter(ResourceMetric.resource_id.in_(
            db.query(Resource.id).filter(Resource.user_id == current_user.id)
        )).delete(synchronize_session=False)
        db.query(Recommendation).filter(Recommendation.user_id == current_user.id).delete()
        db.query(Resource).filter(Resource.user_id == current_user.id).delete()
        db.commit()
        
        # Create comprehensive sample resources (15 resources across teams/environments)
        resources = [
            # Backend Team
            Resource(id="vm-backend-1", name="api-server-prod-01", resource_type="EC2 t3.xlarge", team="Backend", environment="production", waste_score=8.5, user_id=current_user.id),
            Resource(id="vm-backend-2", name="api-server-prod-02", resource_type="EC2 t3.xlarge", team="Backend", environment="production", waste_score=12.3, user_id=current_user.id),
            Resource(id="vm-backend-3", name="worker-queue-prod", resource_type="EC2 c5.2xlarge", team="Backend", environment="production", waste_score=25.7, user_id=current_user.id),
            Resource(id="vm-backend-4", name="api-staging-01", resource_type="EC2 t3.large", team="Backend", environment="staging", waste_score=45.2, user_id=current_user.id),
            
            # Frontend Team
            Resource(id="vm-frontend-1", name="web-server-prod-01", resource_type="EC2 t3.medium", team="Frontend", environment="production", waste_score=15.8, user_id=current_user.id),
            Resource(id="vm-frontend-2", name="web-server-prod-02", resource_type="EC2 t3.medium", team="Frontend", environment="production", waste_score=18.2, user_id=current_user.id),
            Resource(id="vm-frontend-3", name="web-dev-01", resource_type="EC2 t3.large", team="Frontend", environment="development", waste_score=78.5, user_id=current_user.id),
            
            # Platform Team
            Resource(id="vm-platform-1", name="cache-redis-prod", resource_type="ElastiCache r6g.large", team="Platform", environment="production", waste_score=22.1, user_id=current_user.id),
            Resource(id="vm-platform-2", name="cache-staging", resource_type="ElastiCache r6g.medium", team="Platform", environment="staging", waste_score=52.3, user_id=current_user.id),
            Resource(id="vm-platform-3", name="monitoring-server", resource_type="EC2 t3.medium", team="Platform", environment="production", waste_score=35.6, user_id=current_user.id),
            
            # Data Team
            Resource(id="vm-data-1", name="analytics-worker-01", resource_type="EC2 r5.xlarge", team="Data", environment="production", waste_score=32.4, user_id=current_user.id),
            Resource(id="vm-data-2", name="etl-pipeline-prod", resource_type="EC2 c5.large", team="Data", environment="production", waste_score=28.9, user_id=current_user.id),
            Resource(id="vm-data-3", name="ml-training-dev", resource_type="EC2 p3.2xlarge", team="Data", environment="development", waste_score=85.7, user_id=current_user.id),
            
            # DevOps Team
            Resource(id="vm-devops-1", name="ci-build-agent-01", resource_type="EC2 t3.large", team="DevOps", environment="production", waste_score=42.8, user_id=current_user.id),
            Resource(id="vm-devops-2", name="temp-test-env", resource_type="EC2 t3.xlarge", team="DevOps", environment="development", waste_score=92.3, user_id=current_user.id),
        ]
        db.add_all(resources)
        db.commit()
        
        # Create realistic metrics for each resource (7 days of data)
        now = datetime.utcnow()
        metrics_created = 0
        
        for resource in resources:
            # Create 7 days of hourly metrics (simplified to daily for performance)
            for day in range(7):
                timestamp = now - timedelta(days=day, hours=12)  # Noon each day
                
                # Generate realistic metrics based on waste score
                if resource.waste_score > 70:
                    # High waste - very low utilization
                    cpu = 8.0 + (day * 1.5) + (resource.waste_score * 0.1)
                    memory = 12.0 + (day * 1.2) + (resource.waste_score * 0.08)
                    disk_io = 15.0 + (day * 2)
                    network_io = 10.0 + (day * 1.5)
                elif resource.waste_score > 30:
                    # Medium waste - moderate utilization
                    cpu = 22.0 + (day * 2.5) + (resource.waste_score * 0.3)
                    memory = 28.0 + (day * 2) + (resource.waste_score * 0.25)
                    disk_io = 35.0 + (day * 4)
                    network_io = 25.0 + (day * 3)
                else:
                    # Low waste - good utilization
                    cpu = 55.0 + (day * 3) + (resource.waste_score * 0.5)
                    memory = 60.0 + (day * 2.5) + (resource.waste_score * 0.4)
                    disk_io = 65.0 + (day * 5)
                    network_io = 45.0 + (day * 4)
                
                metric = ResourceMetric(
                    resource_id=resource.id,
                    timestamp=timestamp,
                    cpu_utilization=min(max(cpu, 5.0), 95.0),
                    memory_utilization=min(max(memory, 5.0), 95.0),
                    disk_io=min(max(disk_io, 10.0), 200.0),
                    network_io=min(max(network_io, 5.0), 150.0)
                )
                db.add(metric)
                metrics_created += 1
        
        db.commit()
        
        # Create comprehensive recommendations
        recommendations = [
            # Rightsizing recommendations
            Recommendation(
                resource_id="vm-backend-4",
                recommendation_type="rightsizing",
                description="Staging API server consistently uses <30% CPU and <35% memory. Workload can run on smaller instance.",
                potential_savings=145.50,
                suggested_action="Downgrade from t3.large to t3.medium (save $145.50/month)",
                confidence=0.88,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-platform-2",
                recommendation_type="rightsizing",
                description="Cache server in staging shows low memory utilization (<40%) and minimal cache hits.",
                potential_savings=220.00,
                suggested_action="Downgrade from r6g.medium to r6g.small (save $220/month)",
                confidence=0.82,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-data-1",
                recommendation_type="rightsizing",
                description="Analytics worker has 32% waste score. Memory usage peaks at 55%, CPU at 45%.",
                potential_savings=185.75,
                suggested_action="Downgrade from r5.xlarge to r5.large (save $185.75/month)",
                confidence=0.75,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-devops-1",
                recommendation_type="rightsizing",
                description="CI build agent idle 60% of the time. Consider spot instances or smaller base instance.",
                potential_savings=95.30,
                suggested_action="Switch to t3.medium + spot instances (save $95.30/month)",
                confidence=0.80,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-platform-3",
                recommendation_type="rightsizing",
                description="Monitoring server over-provisioned. Current usage: 35% CPU, 40% memory.",
                potential_savings=72.50,
                suggested_action="Downgrade from t3.medium to t3.small (save $72.50/month)",
                confidence=0.85,
                user_id=current_user.id
            ),
            
            # Schedule recommendations
            Recommendation(
                resource_id="vm-frontend-3",
                recommendation_type="schedule",
                description="Development web server runs 24/7 but only used during business hours (9 AM - 6 PM).",
                potential_savings=285.00,
                suggested_action="Auto-shutdown: Daily 6 PM - 9 AM + weekends (save $285/month)",
                confidence=0.92,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-data-3",
                recommendation_type="schedule",
                description="ML training instance in dev environment idle 85% of the time. Very expensive GPU instance.",
                potential_savings=1850.00,
                suggested_action="Terminate when idle >30 min, use on-demand only (save $1,850/month)",
                confidence=0.95,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-devops-2",
                recommendation_type="schedule",
                description="Temporary test environment left running continuously. Should be ephemeral.",
                potential_savings=420.00,
                suggested_action="Auto-terminate after 2 hours of inactivity (save $420/month)",
                confidence=0.98,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-backend-4",
                recommendation_type="schedule",
                description="Staging API server can run on reduced schedule outside business hours.",
                potential_savings=125.00,
                suggested_action="Scale down to 1 instance after 8 PM (save $125/month)",
                confidence=0.78,
                user_id=current_user.id
            ),
            Recommendation(
                resource_id="vm-platform-2",
                recommendation_type="schedule",
                description="Staging cache server not needed overnight or weekends.",
                potential_savings=165.00,
                suggested_action="Auto-shutdown: Daily 10 PM - 7 AM + weekends (save $165/month)",
                confidence=0.85,
                user_id=current_user.id
            ),
        ]
        db.add_all(recommendations)
        db.commit()
        
        logger.info(f"Successfully seeded database: {len(resources)} resources, {metrics_created} metrics, {len(recommendations)} recommendations")
        
        return {
            "status": "success",
            "message": "Seeded with comprehensive demo data",
            "resources_created": len(resources),
            "metrics_created": metrics_created,
            "recommendations_created": len(recommendations),
            "teams": ["Backend", "Frontend", "Platform", "Data", "DevOps"],
            "environments": ["production", "staging", "development"]
        }
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
