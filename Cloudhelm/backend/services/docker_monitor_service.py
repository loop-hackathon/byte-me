"""
Docker container monitoring service.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging

from backend.models.health import ContainerMetric

logger = logging.getLogger(__name__)

# Try to import Docker SDK
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    logger.warning("Docker SDK not available")
    DOCKER_AVAILABLE = False


class DockerMonitorService:
    """Service for Docker container monitoring."""
    
    def __init__(self):
        """Initialize Docker client if available."""
        self.client = None
        
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                # Test connection
                self.client.ping()
                logger.info("Docker client initialized successfully")
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """
        Check if Docker is available.
        
        Returns:
            True if Docker is available, False otherwise
        """
        return self.client is not None
    
    def discover_containers(self, include_stopped: bool = False) -> List[Dict]:
        """
        Discover Docker containers.
        
        Args:
            include_stopped: Include stopped containers
        
        Returns:
            List of container information dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            containers = self.client.containers.list(all=include_stopped)
            
            container_list = []
            for container in containers:
                container_info = {
                    'container_id': container.id[:12],  # Short ID
                    'container_name': container.name,
                    'image': container.image.tags[0] if container.image.tags else container.image.id[:12],
                    'status': container.status,
                    'created': container.attrs['Created'],
                    'ports': self._format_ports(container.ports)
                }
                container_list.append(container_info)
            
            logger.debug(f"Discovered {len(container_list)} containers")
            return container_list
        
        except Exception as e:
            logger.error(f"Error discovering containers: {e}")
            return []
    
    def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """
        Get real-time statistics for a container.
        
        Args:
            container_id: Container ID or name
        
        Returns:
            Container statistics dictionary or None
        """
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Parse CPU stats
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_count = stats['cpu_stats']['online_cpus']
            
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
            
            # Parse memory stats
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 1)
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
            
            # Parse network stats
            networks = stats.get('networks', {})
            network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
            network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
            
            # Parse disk I/O stats
            blkio_stats = stats.get('blkio_stats', {}).get('io_service_bytes_recursive', [])
            disk_read = sum(item['value'] for item in blkio_stats if item.get('op') == 'Read')
            disk_write = sum(item['value'] for item in blkio_stats if item.get('op') == 'Write')
            
            # PIDs
            pids = stats.get('pids_stats', {}).get('current', 0)
            
            return {
                'container_id': container_id,
                'container_name': container.name,
                'timestamp': datetime.utcnow().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_usage_bytes': memory_usage,
                'memory_percent': memory_percent,
                'network_rx_bytes': network_rx,
                'network_tx_bytes': network_tx,
                'disk_read_bytes': disk_read,
                'disk_write_bytes': disk_write,
                'pids': pids
            }
        
        except Exception as e:
            logger.error(f"Error getting container stats for {container_id}: {e}")
            return None
    
    def get_container_logs(
        self,
        container_id: str,
        tail: int = 100
    ) -> List[str]:
        """
        Get container logs.
        
        Args:
            container_id: Container ID or name
            tail: Number of lines to return
        
        Returns:
            List of log lines
        """
        if not self.is_available():
            return []
        
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs.split('\n')
        
        except Exception as e:
            logger.error(f"Error getting logs for {container_id}: {e}")
            return []
    
    def get_system_info(self) -> Optional[Dict]:
        """
        Get Docker system information.
        
        Returns:
            System info dictionary or None
        """
        if not self.is_available():
            return None
        
        try:
            info = self.client.info()
            return {
                'containers': info.get('Containers', 0),
                'containers_running': info.get('ContainersRunning', 0),
                'containers_paused': info.get('ContainersPaused', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0),
                'server_version': info.get('ServerVersion', 'unknown'),
                'operating_system': info.get('OperatingSystem', 'unknown'),
                'architecture': info.get('Architecture', 'unknown')
            }
        
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return None
    
    def monitor_all_containers(self, db: Session) -> List[ContainerMetric]:
        """
        Monitor all running containers and store metrics.
        
        Args:
            db: Database session
        
        Returns:
            List of created ContainerMetric records
        """
        if not self.is_available():
            return []
        
        containers = self.discover_containers(include_stopped=False)
        metrics = []
        
        for container_info in containers:
            stats = self.get_container_stats(container_info['container_id'])
            
            if stats:
                metric = ContainerMetric(
                    container_id=stats['container_id'],
                    container_name=stats['container_name'],
                    timestamp=datetime.utcnow(),
                    cpu_percent=stats['cpu_percent'],
                    memory_usage_bytes=stats['memory_usage_bytes'],
                    memory_percent=stats['memory_percent'],
                    network_rx_bytes=stats['network_rx_bytes'],
                    network_tx_bytes=stats['network_tx_bytes'],
                    disk_read_bytes=stats['disk_read_bytes'],
                    disk_write_bytes=stats['disk_write_bytes'],
                    pids=stats['pids']
                )
                
                db.add(metric)
                metrics.append(metric)
        
        if metrics:
            db.commit()
            logger.info(f"Stored metrics for {len(metrics)} containers")
        
        return metrics
    
    @staticmethod
    def _format_ports(ports: Dict) -> List[str]:
        """
        Format container ports for display.
        
        Args:
            ports: Docker ports dictionary
        
        Returns:
            List of formatted port strings
        """
        formatted = []
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    formatted.append(f"{binding['HostPort']}:{container_port}")
            else:
                formatted.append(container_port)
        return formatted


# Singleton instance
docker_monitor_service = DockerMonitorService()
