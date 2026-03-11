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

  // Overview endpoints
  async getKPISummary(params: {
    time_range?: string;
    environment?: string;
  }): Promise<KPISummary> {
    const queryParams = new URLSearchParams();
    if (params.time_range) queryParams.append('time_range', params.time_range);
    if (params.environment) queryParams.append('environment', params.environment);

    const cacheKey = `kpi-summary-${queryParams.toString()}`;
    
    return this.cachedFetch<KPISummary>(
      `${API_BASE_URL}/api/overview/kpi-summary?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      5 * 60 * 1000 // 5 minutes
    );
  }

  async getCostTimeSeries(params: {
    time_range?: string;
    environment?: string;
  }): Promise<CostTimeSeries> {
    const queryParams = new URLSearchParams();
    if (params.time_range) queryParams.append('time_range', params.time_range);
    if (params.environment) queryParams.append('environment', params.environment);

    const cacheKey = `cost-timeseries-${queryParams.toString()}`;

    return this.cachedFetch<CostTimeSeries>(
      `${API_BASE_URL}/api/overview/cost-timeseries?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      10 * 60 * 1000 // 10 minutes
    );
  }

  async getSpendByTeam(params: {
    time_range?: string;
    environment?: string;
    limit?: number;
  }): Promise<SpendByTeam> {
    const queryParams = new URLSearchParams();
    if (params.time_range) queryParams.append('time_range', params.time_range);
    if (params.environment) queryParams.append('environment', params.environment);
    if (params.limit) queryParams.append('limit', params.limit.toString());

    const cacheKey = `spend-by-team-${queryParams.toString()}`;

    return this.cachedFetch<SpendByTeam>(
      `${API_BASE_URL}/api/overview/spend-by-team?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      10 * 60 * 1000 // 10 minutes
    );
  }

  async getSpendByProvider(params: {
    time_range?: string;
    environment?: string;
  }): Promise<SpendByProvider> {
    const queryParams = new URLSearchParams();
    if (params.time_range) queryParams.append('time_range', params.time_range);
    if (params.environment) queryParams.append('environment', params.environment);

    const cacheKey = `spend-by-provider-${queryParams.toString()}`;

    return this.cachedFetch<SpendByProvider>(
      `${API_BASE_URL}/api/overview/spend-by-provider?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      10 * 60 * 1000 // 10 minutes
    );
  }

  async getOptimizationOpportunities(limit?: number): Promise<OptimizationOpportunities> {
    const queryParams = new URLSearchParams();
    if (limit) queryParams.append('limit', limit.toString());

    const cacheKey = `optimization-opportunities-${queryParams.toString()}`;

    return this.cachedFetch<OptimizationOpportunities>(
      `${API_BASE_URL}/api/overview/optimization-opportunities?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      30 * 60 * 1000 // 30 minutes (expensive computation)
    );
  }

  async getReliabilityMetrics(time_range?: string): Promise<ReliabilityMetrics> {
    const queryParams = new URLSearchParams();
    if (time_range) queryParams.append('time_range', time_range);

    const cacheKey = `reliability-metrics-${queryParams.toString()}`;

    return this.cachedFetch<ReliabilityMetrics>(
      `${API_BASE_URL}/api/overview/reliability-metrics?${queryParams}`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      5 * 60 * 1000 // 5 minutes
    );
  }

  async getDeploymentStats(): Promise<DeploymentStats> {
    const cacheKey = 'deployment-stats';

    return this.cachedFetch<DeploymentStats>(
      `${API_BASE_URL}/api/overview/deployment-stats`,
      {
        headers: this.getHeaders(),
        credentials: 'include',
      },
      cacheKey,
      5 * 60 * 1000 // 5 minutes
    );
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
}

export const api = new ApiClient();

