// Overview Page Types

export interface SpendVsBudget {
  percentage: number;
  status: 'under' | 'at_risk' | 'over';
}

export interface KPIDeltas {
  spend_delta: string;
  anomalies_delta: string;
  incidents_delta: string;
  deployments_delta: string;
}

export interface KPISummary {
  total_cloud_spend: number;
  spend_vs_budget: SpendVsBudget;
  forecasted_month_end: number;
  active_anomalies: number;
  potential_savings: number;
  open_incidents: number;
  availability: number;
  error_rate: number;
  deployments_count: number;
  teams_at_risk: number;
  deltas: KPIDeltas;
}

export interface CostTimeSeriesPoint {
  date: string;
  cost: number;
  forecast: number;
  anomaly: boolean;
}

export interface CostTimeSeries {
  series: CostTimeSeriesPoint[];
  total_cost: number;
  avg_daily_cost: number;
}

export interface SpendByTeamItem {
  team: string;
  spend: number;
}

export interface SpendByTeam {
  breakdown: SpendByTeamItem[];
  total_spend: number;
}

export interface SpendByProviderItem {
  provider: string;
  spend: number;
  percentage: number;
  color: string;
}

export interface SpendByProvider {
  breakdown: SpendByProviderItem[];
  total_spend: number;
}

export interface OptimizationOpportunity {
  resource: string;
  estimated_savings: number;
  type: string;
  recommended_action: string;
  service: string;
  team: string;
}

export interface OptimizationOpportunities {
  opportunities: OptimizationOpportunity[];
  total_potential_savings: number;
}

export interface IncidentItem {
  id: number;
  title: string;
  status: string;
  severity: string;
  duration: string;
  service: string | null;
  team: string | null;
}

export interface MetricWithTrend {
  percentage: number;
  delta: string;
  trend: 'positive' | 'negative';
}

export interface MTTRMetrics {
  average: string;
  median: string;
}

export interface ReliabilityMetrics {
  open_incidents: IncidentItem[];
  availability: MetricWithTrend;
  error_rate: MetricWithTrend;
  mttr: MTTRMetrics;
}

export interface DeploymentItem {
  id: number;
  service: string;
  environment: string;
  status: string;
  deployed_at: string;
  deployed_by: string | null;
  version: string | null;
}

export interface DeploymentStats {
  total_deployments: number;
  successful: number;
  failed: number;
  delta: string;
  recent_deployments: DeploymentItem[];
}
