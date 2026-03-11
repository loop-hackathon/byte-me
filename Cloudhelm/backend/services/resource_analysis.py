"""
Resource analysis engine for calculating waste scores and generating recommendations.
Adapted from Loop_ResourceDashboard for CloudHelm.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

from backend.models.resource import Resource, ResourceMetric, Recommendation

logger = logging.getLogger(__name__)


def calculate_average_metrics(db: Session, resource_id: str, days: int = 7) -> Optional[Dict[str, float]]:
    """
    Calculate average metrics for a resource over the specified time period.
    
    Args:
        db: Database session
        resource_id: Resource ID to analyze
        days: Number of days to look back (default: 7)
    
    Returns:
        Dictionary with average CPU, memory, disk_io, and network_io, or None if no metrics
    """
    # Calculate time window
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    # Query metrics within time window
    metrics = db.query(ResourceMetric).filter(
        ResourceMetric.resource_id == resource_id,
        ResourceMetric.timestamp >= cutoff_time
    ).all()
    
    if not metrics:
        return None
    
    # Calculate averages
    avg_cpu = sum(m.cpu_utilization for m in metrics) / len(metrics)
    avg_memory = sum(m.memory_utilization for m in metrics) / len(metrics)
    
    # Disk and network IO might be None
    disk_values = [m.disk_io for m in metrics if m.disk_io is not None]
    network_values = [m.network_io for m in metrics if m.network_io is not None]
    
    avg_disk = sum(disk_values) / len(disk_values) if disk_values else 0.0
    avg_network = sum(network_values) / len(network_values) if network_values else 0.0
    
    return {
        "cpu": avg_cpu,
        "memory": avg_memory,
        "disk_io": avg_disk,
        "network_io": avg_network,
        "sample_count": len(metrics)
    }


def analyze_resource_utilization(db: Session, resource_id: str, user_id: int) -> float:
    """
    Analyze resource utilization and calculate waste score.
    
    Waste score calculation:
    - 0-100 scale, higher = more waste
    - Based on average CPU and memory utilization
    - If CPU < 30% or Memory < 30%, waste score increases
    - Formula: waste_score = (30 - min(cpu, memory)) / 30 * 100
    
    Args:
        db: Database session
        resource_id: Resource ID to analyze
    
    Returns:
        Waste score (0-100)
    """
    # Get average metrics
    avg_metrics = calculate_average_metrics(db, resource_id)
    
    if not avg_metrics:
        logger.warning(f"No metrics found for resource {resource_id}")
        return 0.0
    
    avg_cpu = avg_metrics["cpu"]
    avg_memory = avg_metrics["memory"]
    
    # Calculate waste score
    # Use the minimum of CPU and memory to determine waste
    min_utilization = min(avg_cpu, avg_memory)
    
    if min_utilization < 30.0:
        # High waste if utilization is low
        waste_score = (30.0 - min_utilization) / 30.0 * 100.0
    else:
        # Low waste if utilization is reasonable
        waste_score = 0.0
    
    # Update resource waste score
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == user_id
    ).first()
    if resource:
        resource.waste_score = waste_score
        db.commit()
        logger.info(f"Updated waste score for {resource.name}: {waste_score:.2f}")
    
    return waste_score


def generate_rightsizing_recommendation(
    db: Session, 
    resource_id: str,
    user_id: int,
    current_type: str = "t3.large",
    recommended_type: str = "t3.medium",
    monthly_savings: float = 150.0
) -> Optional[Recommendation]:
    """
    Generate a rightsizing recommendation for underutilized resources.
    
    Args:
        db: Database session
        resource_id: Resource ID
        current_type: Current instance type
        recommended_type: Recommended instance type
        monthly_savings: Estimated monthly savings in USD
    
    Returns:
        Created recommendation or None if already exists
    """
    # Check if recommendation already exists to avoid duplicates
    existing = db.query(Recommendation).filter(
        Recommendation.resource_id == resource_id,
        Recommendation.recommendation_type == 'rightsizing',
        Recommendation.user_id == user_id
    ).first()
    
    if existing:
        logger.info(f"Rightsizing recommendation already exists for resource {resource_id}")
        return None
    
    # Get average metrics
    avg_metrics = calculate_average_metrics(db, resource_id)
    
    if not avg_metrics:
        logger.warning(f"No metrics found for resource {resource_id}")
        return None
    
    avg_cpu = avg_metrics["cpu"]
    avg_memory = avg_metrics["memory"]
    
    # Only recommend rightsizing if utilization is low
    if avg_cpu < 20.0 or avg_memory < 20.0:
        resource = db.query(Resource).filter(
            Resource.id == resource_id,
            Resource.user_id == user_id
        ).first()
        
        if not resource:
            return None
        
        # Create recommendation
        rec = Recommendation(
            resource_id=resource_id,
            recommendation_type='rightsizing',
            description=f'Resource is significantly underutilized (CPU: {avg_cpu:.1f}%, Memory: {avg_memory:.1f}%).',
            potential_savings=monthly_savings,
            suggested_action=f'Downgrade from {current_type} to {recommended_type}',
            confidence=0.85,
            user_id=user_id
        )
        
        db.add(rec)
        db.commit()
        db.refresh(rec)
        
        logger.info(f"Created rightsizing recommendation for {resource.name}: ${monthly_savings}/month")
        return rec
    
    return None


def generate_schedule_recommendation(
    db: Session,
    resource_id: str,
    user_id: int,
    schedule: str = "Shutdown daily 8 PM - 8 AM",
    monthly_savings: float = 50.0
) -> Optional[Recommendation]:
    """
    Generate a schedule recommendation for non-production resources.
    
    Args:
        db: Database session
        resource_id: Resource ID
        schedule: Suggested schedule
        monthly_savings: Estimated monthly savings in USD
    
    Returns:
        Created recommendation or None if already exists or not applicable
    """
    # Check if recommendation already exists
    existing = db.query(Recommendation).filter(
        Recommendation.resource_id == resource_id,
        Recommendation.recommendation_type == 'schedule',
        Recommendation.user_id == user_id
    ).first()
    
    if existing:
        logger.info(f"Schedule recommendation already exists for resource {resource_id}")
        return None
    
    # Get resource
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == user_id
    ).first()
    
    if not resource:
        return None
    
    # Only recommend scheduling for non-production environments
    if resource.environment.lower() != 'production':
        # Create recommendation
        rec = Recommendation(
            resource_id=resource_id,
            recommendation_type='schedule',
            description=f'Non-production resource running 24/7 in {resource.environment} environment.',
            potential_savings=monthly_savings,
            suggested_action=schedule,
            confidence=0.90,
            user_id=user_id
        )
        
        db.add(rec)
        db.commit()
        db.refresh(rec)
        
        logger.info(f"Created schedule recommendation for {resource.name}: ${monthly_savings}/month")
        return rec
    
    return None


class ResourceAnalysisService:
    """Service for resource efficiency analysis and recommendations."""
    
    @staticmethod
    def analyze_all_resources(db: Session, user_id: int) -> Dict[str, int]:
        """
        Analyze all resources and generate recommendations for a user.
        
        Returns:
            Dictionary with counts of analyzed resources and generated recommendations
        """
        resources = db.query(Resource).filter(Resource.user_id == user_id).all()
        
        analyzed_count = 0
        rightsizing_count = 0
        schedule_count = 0
        
        for resource in resources:
            # Analyze utilization
            analyze_resource_utilization(db, resource.id, user_id)
            analyzed_count += 1
            
            # Generate recommendations
            if generate_rightsizing_recommendation(db, resource.id, user_id):
                rightsizing_count += 1
            
            if generate_schedule_recommendation(db, resource.id, user_id):
                schedule_count += 1
        
        logger.info(f"Analyzed {analyzed_count} resources, generated {rightsizing_count} rightsizing and {schedule_count} schedule recommendations")
        
        return {
            "analyzed": analyzed_count,
            "rightsizing_recommendations": rightsizing_count,
            "schedule_recommendations": schedule_count
        }


# Singleton instance
resource_analysis_service = ResourceAnalysisService()
