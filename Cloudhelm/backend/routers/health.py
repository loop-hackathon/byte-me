"""
Health monitoring router for CloudHelm.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import logging
import json

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.health import MetricsAnomaly
from backend.schemas.health import (
    HealthSummaryResponse,
    AnomalyResponse,
    MetricHistoryResponse,
    ServiceRegisterRequest,
    ServiceResponse,
    ContainerResponse,
    ContainerStatsResponse,
    PodResponse,
    DeploymentResponse,
    ClusterHealthResponse,
    DemoDataRequest,
    DemoDataResponse,
    InfrastructureAvailability,
    LatencyResponse,
    ResourcesResponse
)
from backend.services.health_service import health_service
from backend.services.anomaly_detection_service import anomaly_detection_service
from backend.services.docker_monitor_service import docker_monitor_service
from backend.services.kubernetes_monitor_service import kubernetes_monitor_service
from backend.services.demo_data_service import demo_data_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


# Health Monitoring Endpoints

@router.get("/summary", response_model=List[HealthSummaryResponse])
def get_health_summary(
    service: Optional[str] = Query(None, description="Filter by service name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get health summary for services.
    
    Returns latest metrics with calculated health scores and status.
    """
    try:
        summaries = health_service.get_health_summary(db, service_name=service)
        
        # Convert to response format
        response = []
        for summary in summaries:
            response.append(HealthSummaryResponse(
                service_name=summary['service_name'],
                timestamp=summary['timestamp'],
                request_rate=summary['request_rate'],
                error_rate=summary['error_rate'],
                latency=LatencyResponse(
                    p50=summary['latency']['p50'],
                    p95=summary['latency']['p95'],
                    p99=summary['latency']['p99']
                ),
                resources=ResourcesResponse(
                    cpu=summary['resources']['cpu'],
                    memory=summary['resources']['memory']
                ),
                restart_count=summary['restart_count'],
                pod_count=summary['pod_count'],
                health_score=summary['health_score'],
                status=summary['status']
            ))
        
        return response
    
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies", response_model=List[AnomalyResponse])
def get_anomalies(
    service: Optional[str] = Query(None, description="Filter by service name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detected anomalies with optional filtering.
    
    Returns anomalies ordered by timestamp (most recent first).
    """
    try:
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query
        query = db.query(MetricsAnomaly).filter(
            MetricsAnomaly.timestamp >= cutoff_time
        )
        
        if service:
            query = query.filter(MetricsAnomaly.service_name == service)
        
        if severity:
            query = query.filter(MetricsAnomaly.severity == severity)
        
        anomalies = query.order_by(desc(MetricsAnomaly.timestamp)).all()
        
        # Convert to response format
        response = []
        for anomaly in anomalies:
            response.append(AnomalyResponse(
                id=str(anomaly.id),
                service_name=anomaly.service_name,
                timestamp=anomaly.timestamp.isoformat(),
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
                anomaly_score=anomaly.anomaly_score,
                affected_metrics=json.loads(anomaly.affected_metrics),
                description=anomaly.description
            ))
        
        return response
    
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history", response_model=List[MetricHistoryResponse])
def get_metrics_history(
    service: str = Query(..., description="Service name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical metrics for a service.
    
    Returns time-series data ordered by timestamp.
    """
    try:
        metrics = health_service.get_metrics_history(db, service, hours)
        
        # Convert to response format
        response = []
        for metric in metrics:
            response.append(MetricHistoryResponse(
                timestamp=metric.timestamp.isoformat(),
                request_rate=metric.request_rate,
                error_rate=metric.error_rate,
                latency_p50=metric.latency_p50,
                latency_p95=metric.latency_p95,
                latency_p99=metric.latency_p99,
                cpu_usage=metric.cpu_usage,
                memory_usage=metric.memory_usage,
                restart_count=metric.restart_count,
                pod_count=metric.pod_count
            ))
        
        return response
    
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/services/register", response_model=ServiceResponse)
def register_service(
    request: ServiceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new service for health monitoring.
    
    Creates or updates service registration.
    """
    try:
        service = health_service.register_service(
            db,
            service_name=request.service_name,
            service_type=request.service_type
        )
        
        return ServiceResponse(
            id=str(service.id),
            service_name=service.service_name,
            service_type=service.service_type,
            status=service.status,
            last_seen=service.last_seen.isoformat() if service.last_seen else None,
            created_at=service.created_at.isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Docker Monitoring Endpoints

@router.get("/docker/containers", response_model=List[ContainerResponse])
def get_docker_containers(
    include_stopped: bool = Query(False, description="Include stopped containers"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Docker containers.
    
    Returns empty list if Docker is not available.
    """
    try:
        if not docker_monitor_service.is_available():
            return []
        
        containers = docker_monitor_service.discover_containers(include_stopped)
        return [ContainerResponse(**container) for container in containers]
    
    except Exception as e:
        logger.error(f"Error getting Docker containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker/containers/{container_id}/stats", response_model=Optional[ContainerStatsResponse])
def get_container_stats(
    container_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time statistics for a Docker container.
    
    Returns None if Docker is not available or container not found.
    """
    try:
        if not docker_monitor_service.is_available():
            return None
        
        stats = docker_monitor_service.get_container_stats(container_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
        
        return ContainerStatsResponse(**stats)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker/containers/{container_id}/logs")
def get_container_logs(
    container_id: str,
    tail: int = Query(100, ge=1, le=1000, description="Number of log lines"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get logs for a Docker container.
    
    Returns empty list if Docker is not available or container not found.
    """
    try:
        if not docker_monitor_service.is_available():
            return {"logs": []}
        
        logs = docker_monitor_service.get_container_logs(container_id, tail)
        return {"logs": logs}
    
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Kubernetes Monitoring Endpoints

@router.get("/kubernetes/pods", response_model=List[PodResponse])
def get_kubernetes_pods(
    namespace: str = Query('default', description="Kubernetes namespace"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Kubernetes pods in a namespace.
    
    Returns empty list if Kubernetes is not available.
    """
    try:
        if not kubernetes_monitor_service.is_available():
            return []
        
        pods = kubernetes_monitor_service.discover_pods(namespace)
        return [PodResponse(**pod) for pod in pods]
    
    except Exception as e:
        logger.error(f"Error getting Kubernetes pods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kubernetes/deployments", response_model=List[DeploymentResponse])
def get_kubernetes_deployments(
    namespace: str = Query('default', description="Kubernetes namespace"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Kubernetes deployments in a namespace.
    
    Returns empty list if Kubernetes is not available.
    """
    try:
        if not kubernetes_monitor_service.is_available():
            return []
        
        deployments = kubernetes_monitor_service.discover_deployments(namespace)
        return [DeploymentResponse(**deployment) for deployment in deployments]
    
    except Exception as e:
        logger.error(f"Error getting Kubernetes deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kubernetes/cluster/health", response_model=Optional[ClusterHealthResponse])
def get_cluster_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Kubernetes cluster health summary.
    
    Returns None if Kubernetes is not available.
    """
    try:
        if not kubernetes_monitor_service.is_available():
            return None
        
        health = kubernetes_monitor_service.get_cluster_health()
        
        if not health:
            return None
        
        return ClusterHealthResponse(**health)
    
    except Exception as e:
        logger.error(f"Error getting cluster health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kubernetes/pods/{pod_name}/logs")
def get_pod_logs(
    pod_name: str,
    namespace: str = Query('default', description="Kubernetes namespace"),
    tail: int = Query(100, ge=1, le=1000, description="Number of log lines"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get logs for a Kubernetes pod.
    
    Returns empty list if Kubernetes is not available or pod not found.
    """
    try:
        if not kubernetes_monitor_service.is_available():
            return {"logs": []}
        
        logs = kubernetes_monitor_service.get_pod_logs(pod_name, namespace, tail)
        return {"logs": logs}
    
    except Exception as e:
        logger.error(f"Error getting pod logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Demo Data Endpoint

@router.post("/demo/generate", response_model=DemoDataResponse)
def generate_demo_data(
    request: DemoDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate demo data for testing.
    
    Creates realistic service metrics with optional anomaly injection.
    """
    try:
        result = demo_data_service.generate_historical_data(
            db,
            hours=request.hours,
            services=request.services,
            anomaly_rate=request.anomaly_rate
        )
        
        return DemoDataResponse(
            services=result['services'],
            metrics_generated=result['metrics_generated'],
            anomalies_injected=result['anomalies_injected'],
            hours=result['hours'],
            message=f"Generated {result['metrics_generated']} metrics for {result['services']} services"
        )
    
    except Exception as e:
        logger.error(f"Error generating demo data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Infrastructure Availability Endpoint

@router.get("/infrastructure/availability", response_model=InfrastructureAvailability)
def get_infrastructure_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check availability of Docker and Kubernetes infrastructure.
    
    Returns availability status for both platforms.
    """
    return InfrastructureAvailability(
        docker_available=docker_monitor_service.is_available(),
        kubernetes_available=kubernetes_monitor_service.is_available()
    )


# Seed Demo Data Endpoint (simplified)

@router.post("/demo/seed")
def seed_demo_health_data(
    hours: int = Query(24, ge=1, le=168, description="Hours of historical data to generate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Seed the database with comprehensive demo health monitoring data.
    
    This creates:
    - Multiple demo services (api-gateway, user-service, payment-service, etc.)
    - Historical metrics for the specified time period
    - Realistic anomalies
    - Service health scores
    """
    try:
        # Register demo services
        demo_services = [
            {"name": "api-gateway", "type": "microservice"},
            {"name": "user-service", "type": "microservice"},
            {"name": "payment-service", "type": "microservice"},
            {"name": "notification-service", "type": "microservice"},
            {"name": "auth-service", "type": "microservice"},
        ]
        
        services_registered = 0
        for svc in demo_services:
            try:
                health_service.register_service(svc["name"], svc["type"])
                services_registered += 1
            except Exception:
                # Service might already exist
                pass
        
        # Generate historical data
        result = demo_data_service.generate_historical_data(
            db,
            hours=hours,
            services=[s["name"] for s in demo_services],
            anomaly_rate=0.05  # 5% anomaly rate
        )
        
        # Run anomaly detection on all services
        anomalies_detected = 0
        for svc in demo_services:
            try:
                anomalies = anomaly_detection_service.detect_anomalies(svc["name"])
                anomalies_detected += len(anomalies)
            except Exception as e:
                logger.warning(f"Could not detect anomalies for {svc['name']}: {e}")
        
        return {
            "success": True,
            "services_registered": services_registered,
            "metrics_generated": result['metrics_generated'],
            "anomalies_detected": anomalies_detected,
            "hours": hours,
            "message": f"Successfully seeded {hours} hours of health monitoring data for {services_registered} services"
        }
    
    except Exception as e:
        logger.error(f"Error seeding demo data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
