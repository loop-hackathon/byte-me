import type { User } from '../types/user';
import type {
  CostSummaryResponse,
  CostAnomaly,
  BudgetStatus,
  UploadResponse,
  ForecastResponse
} from '../types/cost';
import type {
  KPISummary,
  CostTimeSeries,
  SpendByTeam,
  SpendByProvider,
  OptimizationOpportunities,
  ReliabilityMetrics,
  DeploymentStats
} from '../types/overview';
import type {
  Repository,
  Release,
  ReleaseImpact
} from '../types/release';
import type {
  ServiceHealth,
  Anomaly,
  MetricHistory,
  Container,
  ContainerStats,
  Pod,
  Deployment,
  ClusterHealth,
  InfrastructureAvailability,
  TimeWindow
} from '../types/health';
import { apiCache } from './cache';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      if (response.status === 401) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
      
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  private async cachedFetch<T>(
    url: string,
    options: RequestInit,
    cacheKey: string,
    cacheTTL: number = 5 * 60 * 1000 // 5 minutes default
  ): Promise<T> {
    // Check cache first
    const cached = apiCache.get<T>(cacheKey);
    if (cached) {
      return cached;
    }

    // Fetch from API
    const response = await fetch(url, options);
    const data = await this.handleResponse<T>(response);

    // Cache the response
    apiCache.set(cacheKey, data, cacheTTL);

    return data;
  }

  // Auth endpoints
  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<User>(response);
  }

  async logout(): Promise<void> {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    localStorage.removeItem('access_token');
  }

  // Cost endpoints
  async getCostSummary(params: {
    from?: string;
    to?: string;
    group_by?: string;
    env?: string;
  }): Promise<CostSummaryResponse> {
    const queryParams = new URLSearchParams();
    if (params.from) queryParams.append('from', params.from);
    if (params.to) queryParams.append('to', params.to);
    if (params.group_by) queryParams.append('group_by', params.group_by);
    if (params.env) queryParams.append('env', params.env);

    const response = await fetch(
      `${API_BASE_URL}/api/cost/summary?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<CostSummaryResponse>(response);
  }

  async getCostAnomalies(params: {
    from?: string;
    to?: string;
    min_severity?: string;
  }): Promise<CostAnomaly[]> {
    const queryParams = new URLSearchParams();
    if (params.from) queryParams.append('from', params.from);
    if (params.to) queryParams.append('to', params.to);
    if (params.min_severity) queryParams.append('min_severity', params.min_severity);

    const response = await fetch(
      `${API_BASE_URL}/api/cost/anomalies?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<CostAnomaly[]>(response);
  }

  async getBudgetStatus(month?: string): Promise<BudgetStatus[]> {
    const queryParams = new URLSearchParams();
    if (month) queryParams.append('month', month);

    const response = await fetch(
      `${API_BASE_URL}/api/cost/budgets/status?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<BudgetStatus[]>(response);
  }

  async getCostForecast(days: number = 7): Promise<ForecastResponse[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/cost/forecast?days=${days}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<ForecastResponse[]>(response);
  }

  async uploadCostFile(provider: 'aws' | 'gcp' | 'azure', file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_BASE_URL}/api/cost/upload/${provider}`,
      {
        method: 'POST',
        headers,
        body: formData,
        credentials: 'include',
      }
    );
    return this.handleResponse<UploadResponse>(response);
  }

  async recomputeAggregates(startDate?: string, endDate?: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/cost/recompute-aggregates`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ start_date: startDate, end_date: endDate }),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async recomputeAnomalies(): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/cost/recompute-anomalies`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async seedDemoData(): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/cost/seed-demo`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async analyzeBillingCsv(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_BASE_URL}/api/cost/billing/analyze`,
      {
        method: 'POST',
        headers,
        body: formData,
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  // Overview endpoints
  async getKPISummary(params: {
    time_range?: string;
    environment?: string;
  }): Promise<KPISummary> {
    // Hardcoded for direct display as requested
    return {
      total_cloud_spend: 156340.0,
      spend_vs_budget: { percentage: -8.2, status: 'under' },
      forecasted_month_end: 142800.0,
      active_anomalies: 7,
      potential_savings: 27500.0,
      open_incidents: 2,
      availability: 99.94,
      error_rate: 0.08,
      deployments_count: 34,
      teams_at_risk: 3,
      deltas: {
        spend_delta: '+12.5%',
        anomalies_delta: '-2',
        incidents_delta: '-1',
        deployments_delta: '+6'
      }
    };
  }

  async getCostTimeSeries(params: {
    time_range?: string;
    environment?: string;
  }): Promise<CostTimeSeries> {
    // Hardcoded for direct display as requested
    const series = [];
    const now = new Date();
    for (let i = 0; i < 30; i++) {
        const d = new Date();
        d.setDate(now.getDate() - (29 - i));
        series.push({
            date: d.toISOString().split('T')[0],
            cost: 5200 + Math.random() * 1000 + i * 20,
            forecast: 5200 + i * 20,
            anomaly: Math.random() < 0.1
        });
    }
    return {
      series,
      total_cost: 156340.0,
      avg_daily_cost: 5211.33
    };
  }

  async getSpendByTeam(params: {
    time_range?: string;
    environment?: string;
    limit?: number;
  }): Promise<SpendByTeam> {
    // Hardcoded for direct display as requested
    return {
      breakdown: [
        { team: 'Platform Engineering', spend: 45200.0 },
        { team: 'Data Science', spend: 38600.0 },
        { team: 'Backend Services', spend: 31400.0 },
        { team: 'ML Infrastructure', spend: 24800.0 },
        { team: 'DevOps & SRE', spend: 16340.0 }
      ],
      total_spend: 156340.0
    };
  }

  async getSpendByProvider(params: {
    time_range?: string;
    environment?: string;
  }): Promise<SpendByProvider> {
    // Hardcoded for direct display as requested
    return {
      breakdown: [
        { provider: 'AWS', spend: 94500.0, percentage: 60.4, color: '#FF9900' },
        { provider: 'GCP', spend: 42300.0, percentage: 27.1, color: '#4285F4' },
        { provider: 'AZURE', spend: 19540.0, percentage: 12.5, color: '#0078D4' }
      ],
      total_spend: 156340.0
    };
  }

  async getOptimizationOpportunities(limit?: number): Promise<OptimizationOpportunities> {
    // Hardcoded for direct display as requested
    return {
      opportunities: [
        {
          resource: 'EC2 i3.8xlarge (3 instances)',
          estimated_savings: 12400.0,
          type: 'Over-provisioned',
          recommended_action: 'Downsize to i3.4xlarge',
          service: 'EC2',
          team: 'Engineering'
        },
        {
          resource: 'RDS db.r5.4xlarge',
          estimated_savings: 8200.0,
          type: 'Idle',
          recommended_action: 'Stop or delete unused DB',
          service: 'RDS',
          team: 'Data Science'
        },
        {
          resource: 'S3 Glacier Storage',
          estimated_savings: 4800.0,
          type: 'Unused',
          recommended_action: 'Delete old backups',
          service: 'S3',
          team: 'DevOps'
        },
        {
          resource: 'EBS Volumes (unattached)',
          estimated_savings: 2100.0,
          type: 'Idle',
          recommended_action: 'Delete unattached volumes',
          service: 'EBS',
          team: 'Engineering'
        }
      ],
      total_potential_savings: 27500.0
    };
  }

  async getReliabilityMetrics(time_range?: string): Promise<ReliabilityMetrics> {
    // Hardcoded for direct display as requested
    return {
      open_incidents: [
        {
          id: 1001,
          title: 'High latency on stripe-billing-service',
          status: 'investigating',
          severity: 'high',
          duration: '3h',
          service: 'stripe-billing-service',
          team: 'Backend Services'
        },
        {
          id: 1002,
          title: 'Memory leak in tensorflow-inference-api',
          status: 'open',
          severity: 'medium',
          duration: '1d',
          service: 'tensorflow-inference-api',
          team: 'ML Infrastructure'
        }
      ],
      availability: { percentage: 99.94, delta: '+0.02%', trend: 'positive' },
      error_rate: { percentage: 0.08, delta: '-0.03%', trend: 'positive' },
      mttr: { average: '45m', median: '30m' }
    };
  }

  async getDeploymentStats(): Promise<DeploymentStats> {
    // Hardcoded for direct display as requested
    return {
      total_deployments: 34,
      successful: 31,
      failed: 3,
      delta: '+6',
      recent_deployments: [
        {
            id: 5001,
            service: 'nginx-ingress-controller',
            environment: 'prod',
            status: 'success',
            deployed_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            deployed_by: 'ci-pipeline',
            version: 'v2.14.3'
        },
        {
            id: 5002,
            service: 'identity-auth-service',
            environment: 'prod',
            status: 'success',
            deployed_at: new Date(Date.now() - 3600000 * 6).toISOString(),
            deployed_by: 'ci-pipeline',
            version: 'v1.8.0'
        }
      ]
    };
  }

  // Release endpoints
  async listRepositories(): Promise<Repository[]> {
    const response = await fetch(
      `${API_BASE_URL}/repos`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Repository[]>(response);
  }

  async syncRepositories(githubToken?: string): Promise<Repository[]> {
    const headers = this.getHeaders() as Record<string, string>;
    if (githubToken) {
      headers['X-GitHub-Token'] = githubToken;
    }

    const response = await fetch(
      `${API_BASE_URL}/repos/github/user-repos`,
      {
        headers,
        credentials: 'include',
      }
    );
    return this.handleResponse<Repository[]>(response);
  }

  async getRepository(repoId: string): Promise<Repository> {
    const response = await fetch(
      `${API_BASE_URL}/repos/${repoId}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Repository>(response);
  }

  async syncRepository(owner: string, repo: string, githubToken?: string): Promise<any> {
    const headers = this.getHeaders() as Record<string, string>;
    if (githubToken) {
      headers['X-GitHub-Token'] = githubToken;
    }

    const response = await fetch(
      `${API_BASE_URL}/repos/sync`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ owner, repo }),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async syncRepositoryReleases(repoId: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/repos/${repoId}/sync-releases`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getRepositoryReleases(repoId: string): Promise<Release[]> {
    const response = await fetch(
      `${API_BASE_URL}/repos/${repoId}/releases`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Release[]>(response);
  }

  async listReleases(params?: {
    repo_id?: string;
    risk_level?: string;
    limit?: number;
  }): Promise<Release[]> {
    const queryParams = new URLSearchParams();
    if (params?.repo_id) queryParams.append('repo_id', params.repo_id);
    if (params?.risk_level) queryParams.append('risk_level', params.risk_level);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const response = await fetch(
      `${API_BASE_URL}/releases?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Release[]>(response);
  }

  async getRelease(releaseId: string): Promise<Release> {
    const response = await fetch(
      `${API_BASE_URL}/releases/${releaseId}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Release>(response);
  }

  async getReleaseImpact(releaseId: string): Promise<ReleaseImpact> {
    const response = await fetch(
      `${API_BASE_URL}/releases/${releaseId}/impact`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<ReleaseImpact>(response);
  }

  async scanRepositorySecurity(repoId: string, ref?: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/repos/${repoId}/scan`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
        body: ref ? JSON.stringify({ ref }) : undefined,
      }
    );
    return this.handleResponse(response);
  }

  // Resource Efficiency endpoints
  async ingestMetrics(data: {
    resource_id: string;
    resource_name?: string;
    resource_type?: string;
    team?: string;
    environment?: string;
    cpu_utilization: number;
    memory_utilization: number;
    disk_io?: number;
    network_io?: number;
    timestamp?: string;
  }): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/resources/ingest`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getResourceStats(queryString?: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/resources/stats${queryString ? `?${queryString}` : ''}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async listResources(queryString?: string): Promise<any[]> {
    const response = await fetch(
      `${API_BASE_URL}/resources${queryString ? `?${queryString}` : ''}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<any[]>(response);
  }

  async listRecommendations(queryString?: string): Promise<any[]> {
    const response = await fetch(
      `${API_BASE_URL}/resources/recommendations${queryString ? `?${queryString}` : ''}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<any[]>(response);
  }

  async seedResourceData(): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/resources/seed`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  // Resource Efficiency Analysis
  async uploadGrafanaCsv(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${API_BASE_URL}/efficiency/upload-grafana`, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'include',
    });
    return this.handleResponse(response);
  }

  async uploadGeminiCsv(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${API_BASE_URL}/efficiency/upload-gemini`, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'include',
    });
    return this.handleResponse(response);
  }

  async getEfficiencyAnalysis(): Promise<any> {
    // Hardcoded for direct display as requested
    return {
      "scatter_data": [
        {"service": "nginx-ingress-controller", "cpu_pct": 15, "cost": 2500, "efficiency": 0.32},
        {"service": "identity-auth-service", "cpu_pct": 45, "cost": 1200, "efficiency": 0.85},
        {"service": "stripe-billing-service", "cpu_pct": 78, "cost": 3400, "efficiency": 0.92},
        {"service": "redis-session-cache", "cpu_pct": 12, "cost": 800, "efficiency": 0.45},
        {"service": "tensorflow-inference-api", "cpu_pct": 65, "cost": 5600, "efficiency": 0.72},
        {"service": "postgres-primary-rds", "cpu_pct": 52, "cost": 1850, "efficiency": 0.78},
        {"service": "elasticsearch-logging", "cpu_pct": 38, "cost": 2200, "efficiency": 0.61},
        {"service": "kafka-event-broker", "cpu_pct": 71, "cost": 1600, "efficiency": 0.88},
        {"service": "sendgrid-mailer", "cpu_pct": 8, "cost": 450, "efficiency": 0.35},
        {"service": "cloudfront-cdn", "cpu_pct": 22, "cost": 980, "efficiency": 0.55}
      ],
      "recommendations": [
        "Right-size nginx-ingress-controller: save $1,200/mo (CPU at 15%, overpaying)",
        "Shutdown idle sendgrid-mailer instances during off-peak (CPU at 8%)",
        "Consolidate redis-session-cache into fewer m5.large nodes",
        "Review tensorflow-inference-api: high cost at $5,600/mo — consider spot instances",
        "Downgrade elasticsearch-logging to t3.medium (38% avg CPU)"
      ],
      "avg_efficiency": 0.64
    };
  }

  // Health Monitoring endpoints
  async getHealthSummary(service?: string): Promise<ServiceHealth[]> {
    const queryParams = new URLSearchParams();
    if (service) queryParams.append('service', service);

    const cacheKey = `health-summary-${queryParams.toString()}`;

    return this.cachedFetch<ServiceHealth[]>(
      `${API_BASE_URL}/health/summary?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      1 * 60 * 1000 // 1 minute cache for health data
    );
  }

  async getAnomalies(params: {
    service?: string;
    hours?: number;
    severity?: string;
  }): Promise<Anomaly[]> {
    const queryParams = new URLSearchParams();
    if (params.service) queryParams.append('service', params.service);
    if (params.hours) queryParams.append('hours', params.hours.toString());
    if (params.severity) queryParams.append('severity', params.severity);

    const response = await fetch(
      `${API_BASE_URL}/health/anomalies?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Anomaly[]>(response);
  }

  async getMetricsHistory(service: string, hours: number = 24): Promise<MetricHistory[]> {
    const queryParams = new URLSearchParams();
    queryParams.append('service', service);
    queryParams.append('hours', hours.toString());

    const cacheKey = `metrics-history-${service}-${hours}`;

    return this.cachedFetch<MetricHistory[]>(
      `${API_BASE_URL}/health/metrics/history?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      2 * 60 * 1000 // 2 minutes cache
    );
  }

  async registerService(serviceName: string, serviceType: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/health/services/register`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ service_name: serviceName, service_type: serviceType }),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getDockerContainers(includeStopped: boolean = false): Promise<Container[]> {
    const queryParams = new URLSearchParams();
    if (includeStopped) queryParams.append('include_stopped', 'true');

    const response = await fetch(
      `${API_BASE_URL}/health/docker/containers?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Container[]>(response);
  }

  async getContainerStats(containerId: string): Promise<ContainerStats | null> {
    const response = await fetch(
      `${API_BASE_URL}/health/docker/containers/${containerId}/stats`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<ContainerStats | null>(response);
  }

  async getContainerLogs(containerId: string, tail: number = 100): Promise<{ logs: string[] }> {
    const queryParams = new URLSearchParams();
    queryParams.append('tail', tail.toString());

    const response = await fetch(
      `${API_BASE_URL}/health/docker/containers/${containerId}/logs?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<{ logs: string[] }>(response);
  }

  async getKubernetesPods(namespace: string = 'default'): Promise<Pod[]> {
    const queryParams = new URLSearchParams();
    queryParams.append('namespace', namespace);

    const response = await fetch(
      `${API_BASE_URL}/health/kubernetes/pods?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Pod[]>(response);
  }

  async getKubernetesDeployments(namespace: string = 'default'): Promise<Deployment[]> {
    const queryParams = new URLSearchParams();
    queryParams.append('namespace', namespace);

    const response = await fetch(
      `${API_BASE_URL}/health/kubernetes/deployments?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<Deployment[]>(response);
  }

  async getClusterHealth(): Promise<ClusterHealth | null> {
    const response = await fetch(
      `${API_BASE_URL}/health/kubernetes/cluster/health`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<ClusterHealth | null>(response);
  }

  async getPodLogs(podName: string, namespace: string = 'default', tail: number = 100): Promise<{ logs: string[] }> {
    const queryParams = new URLSearchParams();
    queryParams.append('namespace', namespace);
    queryParams.append('tail', tail.toString());

    const response = await fetch(
      `${API_BASE_URL}/health/kubernetes/pods/${podName}/logs?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse<{ logs: string[] }>(response);
  }

  async generateDemoData(params: {
    hours?: number;
    services?: string[];
    anomaly_rate?: number;
  }): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/health/demo/generate`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(params),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getInfrastructureAvailability(): Promise<InfrastructureAvailability> {
    const cacheKey = 'infrastructure-availability';

    return this.cachedFetch<InfrastructureAvailability>(
      `${API_BASE_URL}/health/infrastructure/availability`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      5 * 60 * 1000 // 5 minutes cache
    );
  }

  async seedHealthData(hours: number = 24): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('hours', hours.toString());

    const response = await fetch(
      `${API_BASE_URL}/health/demo/seed?${queryParams}`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  // Incident Management
  async listIncidents(params?: {
    status?: string;
    severity?: string;
    service?: string;
    limit?: number;
  }): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.severity) queryParams.append('severity', params.severity);
    if (params?.service) queryParams.append('service', params.service);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const response = await fetch(
      `${API_BASE_URL}/incidents?${queryParams}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getIncident(id: number): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${id}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async createIncident(data: any): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/incidents`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(data),
      }
    );
    return this.handleResponse(response);
  }

  async updateIncident(id: number, data: any): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${id}`,
      {
        method: 'PATCH',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(data),
      }
    );
    return this.handleResponse(response);
  }

  async deleteIncident(id: number): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${id}`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    if (!response.ok) {
      throw new Error('Failed to delete incident');
    }
  }

  async generateIncidentSummary(id: number): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${id}/generate-summary`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getIncidentSummary(id: number): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${id}/summary`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  // Assistant API
  async queryAssistant(data: {
    repository_id?: string;
    repository_name?: string;
    query: string;
    code_snippet?: string;
    context_type?: 'general' | 'incident' | 'security';
  }): Promise<{ response: string; repository_name?: string }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/query`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(data),
      }
    );
    return this.handleResponse(response);
  }

  async getAssistantStatus(): Promise<{ enabled: boolean; model?: string; service: string }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/status`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  // Advanced Assistant Features
  async delegateTask(data: {
    task_description: string;
    agent_type: string;
    repository_name: string;
    context?: any;
  }): Promise<{ task_id: string; message: string; status: string }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/delegate-task`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(data),
      }
    );
    return this.handleResponse(response);
  }

  async getTaskStatus(taskId: string): Promise<{
    task_id: string;
    description: string;
    agent_type: string;
    status: string;
    repository: string;
    result?: string;
    error?: string;
  }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/task-status/${taskId}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async listActiveTasks(): Promise<{
    active_tasks: any[];
    completed_tasks: any[];
  }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/active-tasks`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getAvailableAgents(): Promise<{ agents: any }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/available-agents`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async askInteractiveQuestions(data: {
    questions: any[];
    repository_name: string;
  }): Promise<{ response: string; repository_name?: string }> {
    const response = await fetch(
      `${API_BASE_URL}/api/assistant/ask-questions`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(data),
      }
    );
    return this.handleResponse(response);
  }

  // Tracing (Tempo Proxy)
  async listTraces(limit: number = 20, project?: string): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    if (project && project.trim() !== '') {
      queryParams.append('project', project.trim());
    }

    const response = await fetch(
      `${API_BASE_URL}/tracing/traces?${queryParams.toString()}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async getTrace(traceId: string): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/tracing/traces/${traceId}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }
}

export const api = new ApiClient();


