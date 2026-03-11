"""
Demo data generation service for testing health monitoring without live infrastructure.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random
import logging

from backend.models.health import ServiceMetric
from backend.services.health_service import health_service

logger = logging.getLogger(__name__)


class DemoDataService:
    """Service for generating realistic demo data."""
    
    @staticmethod
    def generate_realistic_metrics(
        service_name: str,
        timestamp: datetime,
        variation: str = 'normal'
    ) -> Dict:
        """
        Generate realistic service metrics with specified variation pattern.
        
        Args:
            service_name: Service name
            timestamp: Timestamp for metrics
            variation: Pattern type ('normal', 'spike', 'degraded')
        
        Returns:
            Dictionary of metric values
        """
        # Base values for normal operation
        base_metrics = {
            'request_rate': 100.0,
            'error_rate': 0.01,  # 1% error rate
            'latency_p50': 50.0,
            'latency_p95': 150.0,
            'latency_p99': 300.0,
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'restart_count': 0,
            'pod_count': 3
        }
        
        if variation == 'normal':
            # Add small random variations
            metrics = {
                'request_rate': base_metrics['request_rate'] * random.uniform(0.8, 1.2),
                'error_rate': base_metrics['error_rate'] * random.uniform(0.5, 1.5),
                'latency_p50': base_metrics['latency_p50'] * random.uniform(0.9, 1.1),
                'latency_p95': base_metrics['latency_p95'] * random.uniform(0.9, 1.1),
                'latency_p99': base_metrics['latency_p99'] * random.uniform(0.9, 1.1),
                'cpu_usage': base_metrics['cpu_usage'] * random.uniform(0.8, 1.2),
                'memory_usage': base_metrics['memory_usage'] * random.uniform(0.9, 1.1),
                'restart_count': base_metrics['restart_count'],
                'pod_count': base_metrics['pod_count']
            }
        
        elif variation == 'spike':
            # Simulate traffic spike with increased errors and latency
            metrics = {
                'request_rate': base_metrics['request_rate'] * random.uniform(3.0, 5.0),
                'error_rate': base_metrics['error_rate'] * random.uniform(5.0, 10.0),
                'latency_p50': base_metrics['latency_p50'] * random.uniform(2.0, 3.0),
                'latency_p95': base_metrics['latency_p95'] * random.uniform(3.0, 5.0),
                'latency_p99': base_metrics['latency_p99'] * random.uniform(5.0, 10.0),
                'cpu_usage': min(95.0, base_metrics['cpu_usage'] * random.uniform(1.5, 2.0)),
                'memory_usage': min(95.0, base_metrics['memory_usage'] * random.uniform(1.3, 1.8)),
                'restart_count': random.randint(0, 2),
                'pod_count': base_metrics['pod_count']
            }
        
        elif variation == 'degraded':
            # Simulate degraded performance
            metrics = {
                'request_rate': base_metrics['request_rate'] * random.uniform(0.3, 0.6),
                'error_rate': base_metrics['error_rate'] * random.uniform(3.0, 8.0),
                'latency_p50': base_metrics['latency_p50'] * random.uniform(1.5, 2.5),
                'latency_p95': base_metrics['latency_p95'] * random.uniform(2.0, 4.0),
                'latency_p99': base_metrics['latency_p99'] * random.uniform(3.0, 6.0),
                'cpu_usage': base_metrics['cpu_usage'] * random.uniform(1.2, 1.5),
                'memory_usage': base_metrics['memory_usage'] * random.uniform(1.1, 1.4),
                'restart_count': random.randint(1, 3),
                'pod_count': max(1, base_metrics['pod_count'] - random.randint(0, 2))
            }
        
        else:
            metrics = base_metrics
        
        # Ensure values are within valid ranges
        metrics['error_rate'] = min(1.0, max(0.0, metrics['error_rate']))
        metrics['cpu_usage'] = min(100.0, max(0.0, metrics['cpu_usage']))
        metrics['memory_usage'] = min(100.0, max(0.0, metrics['memory_usage']))
        metrics['pod_count'] = max(0, int(metrics['pod_count']))
        metrics['restart_count'] = max(0, int(metrics['restart_count']))
        
        return metrics
    
    @staticmethod
    def generate_historical_data(
        db: Session,
        hours: int = 24,
        services: Optional[List[str]] = None,
        anomaly_rate: float = 0.05
    ) -> Dict[str, int]:
        """
        Generate historical demo data for testing.
        
        Args:
            db: Database session
            hours: Number of hours of historical data
            services: List of service names (defaults to demo services)
            anomaly_rate: Probability of injecting anomalies (0.0-1.0)
        
        Returns:
            Dictionary with counts of generated metrics and anomalies
        """
        if services is None:
            services = [
                'api-gateway',
                'user-service',
                'payment-service',
                'notification-service',
                'analytics-service'
            ]
        
        # Register services
        for service_name in services:
            health_service.register_service(
                db,
                service_name=service_name,
                service_type='microservice'
            )
        
        # Generate metrics at 5-minute intervals
        interval_minutes = 5
        num_intervals = (hours * 60) // interval_minutes
        
        metrics_count = 0
        anomaly_count = 0
        
        for service_name in services:
            for i in range(num_intervals):
                # Calculate timestamp
                timestamp = datetime.utcnow() - timedelta(minutes=(num_intervals - i) * interval_minutes)
                
                # Determine variation pattern
                if random.random() < anomaly_rate:
                    # Inject anomaly
                    variation = random.choice(['spike', 'degraded'])
                    anomaly_count += 1
                else:
                    variation = 'normal'
                
                # Generate metrics
                metrics = DemoDataService.generate_realistic_metrics(
                    service_name,
                    timestamp,
                    variation
                )
                
                # Store metrics
                health_service.collect_metrics(
                    db,
                    service_name=service_name,
                    timestamp=timestamp,
                    **metrics
                )
                
                metrics_count += 1
        
        logger.info(f"Generated {metrics_count} metrics for {len(services)} services over {hours} hours")
        logger.info(f"Injected {anomaly_count} anomalies ({anomaly_rate * 100:.1f}% rate)")
        
        return {
            'services': len(services),
            'metrics_generated': metrics_count,
            'anomalies_injected': anomaly_count,
            'hours': hours
        }
    
    @staticmethod
    def inject_anomaly(
        service_name: str,
        anomaly_type: str = 'spike'
    ) -> Dict:
        """
        Generate a single anomalous metric for immediate testing.
        
        Args:
            service_name: Service name
            anomaly_type: Type of anomaly ('spike' or 'degraded')
        
        Returns:
            Dictionary of anomalous metric values
        """
        timestamp = datetime.utcnow()
        
        metrics = DemoDataService.generate_realistic_metrics(
            service_name,
            timestamp,
            variation=anomaly_type
        )
        
        logger.info(f"Generated {anomaly_type} anomaly for {service_name}")
        return metrics


# Singleton instance
demo_data_service = DemoDataService()
