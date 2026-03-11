"""
Health monitoring service for service health tracking and scoring.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging

from backend.models.health import ServiceMetric, Service

logger = logging.getLogger(__name__)


class HealthService:
    """Service for health monitoring and scoring."""
    
    @staticmethod
    def register_service(
        db: Session,
        service_name: str,
        service_type: str
    ) -> Service:
        """
        Register a new service for health monitoring.
        
        Args:
            db: Database session
            service_name: Name of the service
            service_type: Type of service (microservice, database, cache, etc.)
        
        Returns:
            Created or existing Service
        """
        # Check if service already exists
        existing = db.query(Service).filter(
            Service.service_name == service_name
        ).first()
        
        if existing:
            # Update last_seen and status
            existing.last_seen = datetime.utcnow()
            existing.status = 'active'
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated existing service: {service_name}")
            return existing
        
        # Create new service
        service = Service(
            service_name=service_name,
            service_type=service_type,
            status='active',
            last_seen=datetime.utcnow()
        )
        
        db.add(service)
        db.commit()
        db.refresh(service)
        
        logger.info(f"Registered new service: {service_name} ({service_type})")
        return service
    
    @staticmethod
    def collect_metrics(
        db: Session,
        service_name: str,
        request_rate: float = 0.0,
        error_rate: float = 0.0,
        latency_p50: float = 0.0,
        latency_p95: float = 0.0,
        latency_p99: float = 0.0,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
        restart_count: int = 0,
        pod_count: int = 0,
        timestamp: Optional[datetime] = None
    ) -> ServiceMetric:
        """
        Collect and store service health metrics.
        
        Args:
            db: Database session
            service_name: Name of the service
            request_rate: Requests per second
            error_rate: Error rate (0.0-1.0)
            latency_p50: 50th percentile latency in ms
            latency_p95: 95th percentile latency in ms
            latency_p99: 99th percentile latency in ms
            cpu_usage: CPU usage percentage (0-100)
            memory_usage: Memory usage percentage (0-100)
            restart_count: Number of restarts
            pod_count: Number of pods/instances
            timestamp: Metric timestamp (defaults to now)
        
        Returns:
            Created ServiceMetric
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Check for existing metric at this timestamp
        existing = db.query(ServiceMetric).filter(
            ServiceMetric.service_name == service_name,
            ServiceMetric.timestamp == timestamp
        ).first()
        
        if existing:
            # Update existing metric
            existing.request_rate = request_rate
            existing.error_rate = error_rate
            existing.latency_p50 = latency_p50
            existing.latency_p95 = latency_p95
            existing.latency_p99 = latency_p99
            existing.cpu_usage = cpu_usage
            existing.memory_usage = memory_usage
            existing.restart_count = restart_count
            existing.pod_count = pod_count
            db.commit()
            db.refresh(existing)
            logger.debug(f"Updated metrics for {service_name} at {timestamp}")
            return existing
        
        # Create new metric
        metric = ServiceMetric(
            service_name=service_name,
            timestamp=timestamp,
            request_rate=request_rate,
            error_rate=error_rate,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            restart_count=restart_count,
            pod_count=pod_count
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        logger.debug(f"Collected metrics for {service_name}: error_rate={error_rate:.3f}, latency_p99={latency_p99:.1f}ms")
        return metric
    
    @staticmethod
    def calculate_health_score(metric: ServiceMetric) -> float:
        """
        Calculate health score based on metrics.
        
        Formula: health_score = 100 - (E * 50) - min(L/1000, 30) - min(C, 20)
        Where:
        - E = error_rate (0.0-1.0)
        - L = latency_p99 in milliseconds
        - C = cpu_usage (0-100)
        
        Args:
            metric: ServiceMetric to score
        
        Returns:
            Health score (0-100)
        """
        # Error rate penalty (0-50 points)
        error_penalty = metric.error_rate * 50.0
        
        # Latency penalty (0-30 points)
        # Penalize latency over 1000ms, capped at 30 points
        latency_penalty = min(metric.latency_p99 / 1000.0, 30.0)
        
        # CPU usage penalty (0-20 points)
        # Penalize high CPU usage, capped at 20 points
        cpu_penalty = min(metric.cpu_usage, 20.0)
        
        # Calculate health score
        health_score = 100.0 - error_penalty - latency_penalty - cpu_penalty
        
        # Ensure score is within bounds
        health_score = max(0.0, min(100.0, health_score))
        
        return health_score
    
    @staticmethod
    def get_status_from_health(health_score: float) -> str:
        """
        Classify health status based on health score.
        
        Args:
            health_score: Health score (0-100)
        
        Returns:
            Status string: 'healthy', 'degraded', 'warning', or 'critical'
        """
        if health_score >= 90.0:
            return 'healthy'
        elif health_score >= 70.0:
            return 'degraded'
        elif health_score >= 50.0:
            return 'warning'
        else:
            return 'critical'
    
    @staticmethod
    def get_health_summary(
        db: Session,
        service_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Get health summary for services.
        
        Args:
            db: Database session
            service_name: Optional service name filter
        
        Returns:
            List of health summaries with latest metrics and scores
        """
        # Build query for latest metrics per service
        if service_name:
            # Get latest metric for specific service
            latest_metric = db.query(ServiceMetric).filter(
                ServiceMetric.service_name == service_name
            ).order_by(desc(ServiceMetric.timestamp)).first()
            
            metrics = [latest_metric] if latest_metric else []
        else:
            # Get latest metric for each service
            # This is a simplified approach - in production, use window functions
            services = db.query(Service).filter(Service.status == 'active').all()
            metrics = []
            
            for service in services:
                latest = db.query(ServiceMetric).filter(
                    ServiceMetric.service_name == service.service_name
                ).order_by(desc(ServiceMetric.timestamp)).first()
                
                if latest:
                    metrics.append(latest)
        
        # Build summaries
        summaries = []
        for metric in metrics:
            health_score = HealthService.calculate_health_score(metric)
            status = HealthService.get_status_from_health(health_score)
            
            summary = {
                'service_name': metric.service_name,
                'timestamp': metric.timestamp.isoformat(),
                'request_rate': metric.request_rate,
                'error_rate': metric.error_rate,
                'latency': {
                    'p50': metric.latency_p50,
                    'p95': metric.latency_p95,
                    'p99': metric.latency_p99
                },
                'resources': {
                    'cpu': metric.cpu_usage,
                    'memory': metric.memory_usage
                },
                'restart_count': metric.restart_count,
                'pod_count': metric.pod_count,
                'health_score': health_score,
                'status': status
            }
            
            summaries.append(summary)
        
        return summaries
    
    @staticmethod
    def get_metrics_history(
        db: Session,
        service_name: str,
        hours: int = 24
    ) -> List[ServiceMetric]:
        """
        Get historical metrics for a service.
        
        Args:
            db: Database session
            service_name: Service name
            hours: Number of hours to look back
        
        Returns:
            List of ServiceMetric ordered by timestamp
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = db.query(ServiceMetric).filter(
            ServiceMetric.service_name == service_name,
            ServiceMetric.timestamp >= cutoff_time
        ).order_by(ServiceMetric.timestamp).all()
        
        logger.debug(f"Retrieved {len(metrics)} metrics for {service_name} over {hours} hours")
        return metrics


# Singleton instance
health_service = HealthService()
