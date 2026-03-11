"""
Kubernetes pod and cluster monitoring service.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging

from backend.models.health import PodMetric

logger = logging.getLogger(__name__)

# Try to import Kubernetes client
try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    logger.warning("Kubernetes client not available")
    K8S_AVAILABLE = False


class KubernetesMonitorService:
    """Service for Kubernetes pod and cluster monitoring."""
    
    def __init__(self):
        """Initialize Kubernetes clients if available."""
        self.core_v1 = None
        self.apps_v1 = None
        
        if K8S_AVAILABLE:
            try:
                # Try to load in-cluster config first, then fall back to kubeconfig
                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()
                
                self.core_v1 = client.CoreV1Api()
                self.apps_v1 = client.AppsV1Api()
                
                # Test connection
                self.core_v1.list_namespace()
                logger.info("Kubernetes client initialized successfully")
            except Exception as e:
                logger.warning(f"Kubernetes not available: {e}")
                self.core_v1 = None
                self.apps_v1 = None
    
    def is_available(self) -> bool:
        """
        Check if Kubernetes is available.
        
        Returns:
            True if Kubernetes is available, False otherwise
        """
        return self.core_v1 is not None
    
    def discover_namespaces(self) -> List[str]:
        """
        Discover Kubernetes namespaces.
        
        Returns:
            List of namespace names
        """
        if not self.is_available():
            return []
        
        try:
            namespaces = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        
        except Exception as e:
            logger.error(f"Error discovering namespaces: {e}")
            return []
    
    def discover_pods(
        self,
        namespace: str = 'default',
        label_selector: Optional[str] = None
    ) -> List[Dict]:
        """
        Discover pods in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Optional label selector (e.g., "app=myapp")
        
        Returns:
            List of pod information dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            pod_list = []
            for pod in pods.items:
                # Count ready containers
                ready_containers = sum(
                    1 for status in pod.status.container_statuses or []
                    if status.ready
                )
                total_containers = len(pod.status.container_statuses or [])
                
                # Count restarts
                restart_count = sum(
                    status.restart_count
                    for status in pod.status.container_statuses or []
                )
                
                pod_info = {
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'phase': pod.status.phase,
                    'ready_containers': ready_containers,
                    'total_containers': total_containers,
                    'restart_count': restart_count,
                    'node_name': pod.spec.node_name,
                    'created': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                }
                pod_list.append(pod_info)
            
            logger.debug(f"Discovered {len(pod_list)} pods in namespace {namespace}")
            return pod_list
        
        except Exception as e:
            logger.error(f"Error discovering pods in {namespace}: {e}")
            return []
    
    def discover_deployments(self, namespace: str = 'default') -> List[Dict]:
        """
        Discover deployments in a namespace.
        
        Args:
            namespace: Kubernetes namespace
        
        Returns:
            List of deployment information dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            
            deployment_list = []
            for deployment in deployments.items:
                deployment_info = {
                    'name': deployment.metadata.name,
                    'namespace': deployment.metadata.namespace,
                    'replicas': deployment.spec.replicas,
                    'ready_replicas': deployment.status.ready_replicas or 0,
                    'available_replicas': deployment.status.available_replicas or 0,
                    'updated_replicas': deployment.status.updated_replicas or 0,
                    'created': deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None
                }
                deployment_list.append(deployment_info)
            
            logger.debug(f"Discovered {len(deployment_list)} deployments in namespace {namespace}")
            return deployment_list
        
        except Exception as e:
            logger.error(f"Error discovering deployments in {namespace}: {e}")
            return []
    
    def get_cluster_health(self) -> Optional[Dict]:
        """
        Get cluster health summary.
        
        Returns:
            Cluster health dictionary or None
        """
        if not self.is_available():
            return None
        
        try:
            # Get nodes
            nodes = self.core_v1.list_node()
            total_nodes = len(nodes.items)
            ready_nodes = sum(
                1 for node in nodes.items
                if any(
                    condition.type == 'Ready' and condition.status == 'True'
                    for condition in node.status.conditions or []
                )
            )
            not_ready_nodes = total_nodes - ready_nodes
            
            # Get pods across all namespaces
            pods = self.core_v1.list_pod_for_all_namespaces()
            total_pods = len(pods.items)
            running_pods = sum(1 for pod in pods.items if pod.status.phase == 'Running')
            pending_pods = sum(1 for pod in pods.items if pod.status.phase == 'Pending')
            failed_pods = sum(1 for pod in pods.items if pod.status.phase == 'Failed')
            
            # Get namespaces
            namespaces = self.core_v1.list_namespace()
            total_namespaces = len(namespaces.items)
            
            return {
                'nodes': {
                    'total': total_nodes,
                    'ready': ready_nodes,
                    'not_ready': not_ready_nodes
                },
                'pods': {
                    'total': total_pods,
                    'running': running_pods,
                    'pending': pending_pods,
                    'failed': failed_pods
                },
                'namespaces': total_namespaces
            }
        
        except Exception as e:
            logger.error(f"Error getting cluster health: {e}")
            return None
    
    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str,
        tail: int = 100
    ) -> List[str]:
        """
        Get pod logs.
        
        Args:
            pod_name: Pod name
            namespace: Kubernetes namespace
            tail: Number of lines to return
        
        Returns:
            List of log lines
        """
        if not self.is_available():
            return []
        
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail
            )
            return logs.split('\n')
        
        except Exception as e:
            logger.error(f"Error getting logs for pod {pod_name}: {e}")
            return []
    
    def monitor_pods(
        self,
        db: Session,
        namespace: str = 'default'
    ) -> List[PodMetric]:
        """
        Monitor pods in a namespace and store metrics.
        
        Args:
            db: Database session
            namespace: Kubernetes namespace
        
        Returns:
            List of created PodMetric records
        """
        if not self.is_available():
            return []
        
        pods = self.discover_pods(namespace=namespace)
        metrics = []
        
        for pod_info in pods:
            metric = PodMetric(
                pod_name=pod_info['name'],
                namespace=pod_info['namespace'],
                timestamp=datetime.utcnow(),
                phase=pod_info['phase'],
                ready_containers=pod_info['ready_containers'],
                total_containers=pod_info['total_containers'],
                restart_count=pod_info['restart_count'],
                node_name=pod_info['node_name']
            )
            
            db.add(metric)
            metrics.append(metric)
        
        if metrics:
            db.commit()
            logger.info(f"Stored metrics for {len(metrics)} pods in namespace {namespace}")
        
        return metrics


# Singleton instance
kubernetes_monitor_service = KubernetesMonitorService()
