export interface MetricsHistoryResponse {
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

export interface HealthSummaryResponse {
  service_name: string;
  timestamp: string;
  request_rate: number;
  error_rate: number;
  latency: {
    p50: number;
    p95: number;
    p99: number;
  };
  resources: {
    cpu: number;
    memory: number;
  };
  restart_count: number;
  pod_count: number;
  health_score: number;
  status: string;
}

export interface ReliabilityMetricsResponse {
  open_incidents: Array<{
    id: number;
    title: string;
    status: string;
    severity: string;
    duration: string;
    service: string;
    team: string;
  }>;
  availability: {
    percentage: number;
    delta: string;
    trend: string;
  };
  error_rate: {
    percentage: number;
    delta: string;
    trend: string;
  };
  mttr: {
    average: string;
    median: string;
  };
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchReliabilityMetrics(): Promise<ReliabilityMetricsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/overview/reliability-metrics?time_range=7d`);
  if (!response.ok) {
    throw new Error('Failed to fetch reliability metrics');
  }
  return response.json();
}

export async function fetchHealthSummary(): Promise<HealthSummaryResponse[]> {
  const response = await fetch(`${API_BASE_URL}/health/summary`);
  if (!response.ok) {
    throw new Error('Failed to fetch health summary');
  }
  return response.json();
}

export async function fetchMetricsHistory(serviceName: string): Promise<MetricsHistoryResponse[]> {
  const response = await fetch(`${API_BASE_URL}/health/metrics/history?service=${serviceName}&hours=24`);
  if (!response.ok) {
    throw new Error('Failed to fetch metrics history');
  }
  return response.json();
}
