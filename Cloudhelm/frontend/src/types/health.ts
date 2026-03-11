// Type definitions for health monitoring

export type HealthStatus = 'healthy' | 'degraded' | 'warning' | 'critical';
export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';
export type TimeWindow = '1h' | '6h' | '24h' | '7d';

export interface Latency {
  p50: number;
  p95: number;
  p99: number;
}

export interface Resources {
  cpu: number;
  memory: number;
}

export interface ServiceHealth {
  service_name: string;
  timestamp: string;
  request_rate: number;
  error_rate: number;
  latency: Latency;
  resources: Resources;
  restart_count: number;
  pod_count: number;
  health_score: number;
  status: HealthStatus;
}

export interface Anomaly {
  id: string;
  service_name: string;
  timestamp: string;
  anomaly_type: string;
  severity: AnomalySeverity;
  anomaly_score: number;
  affected_metrics: string[];
  description: string;
}

export interface MetricHistory {
  timestamp: string;
  request_rate: number;
  error_rate: number;
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  cpu_usage: number;
  memory_usage: number;
  restart_count: number;
  pod_count: number;
}

export interface Container {
  id: string;
  container_id: string;
  name: string;
  container_name: string;
  image: string;
  status: string;
  created: string;
  ports: string[];
  stats?: ContainerStats;
}

export interface ContainerStats {
  container_id: string;
  container_name: string;
  timestamp: string;
  cpu_percent: number;
  memory_usage_bytes: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  disk_read_bytes: number;
  disk_write_bytes: number;
  pids: number;
}

export interface Pod {
  uid: string;
  name: string;
  namespace: string;
  phase: string;
  ready_containers: number;
  total_containers: number;
  restart_count: number;
  node_name: string | null;
  created: string | null;
  container_statuses: Array<{
    ready: boolean;
    name: string;
    state: string;
  }>;
}

export interface Deployment {
  name: string;
  namespace: string;
  replicas: number;
  ready_replicas: number;
  available_replicas: number;
  updated_replicas: number;
  created: string | null;
}

export interface ClusterHealth {
  nodes: {
    total: number;
    ready: number;
    not_ready: number;
  };
  pods: {
    total: number;
    running: number;
    pending: number;
    failed: number;
  };
  namespaces: number;
}

export interface InfrastructureAvailability {
  docker_available: boolean;
  kubernetes_available: boolean;
}
