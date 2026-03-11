// Type definitions for release tracking
// Adapted from Release-Impact-feature for CloudHelm

export type RiskLevel = 'Healthy' | 'Suspect' | 'Risky';

export interface Repository {
  id: string;
  name: string;
  full_name: string;
  description: string;
  language: string;
  stars: number;
  last_deployment: string;
}

export interface Release {
  id: string;
  repo_id: string;
  service: string;
  version: string;
  commit: string;
  branch: string;
  deployed_at: string;
  status: 'success' | 'failed' | 'pending';
  risk_score: number;
  risk_level: RiskLevel;
  deployment_duration?: number;
  triggered_by?: string;
}

export interface Anomaly {
  id: string;
  release_id: string;
  metric_name: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  value: number;
  expected_value: number;
  deviation: number;
  type: 'metric' | 'cost';
}

export interface Incident {
  id: string;
  title: string;
  description?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  resolved_at: string | null;
  status: 'open' | 'investigating' | 'resolved';
  affected_services: string[];
}

export interface ReleaseImpact {
  release_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  anomaly_count: {
    total: number;
    metric: number;
    cost: number;
  };
  incident_count: number;
  cost_delta: {
    amount: number;
    percentage: number;
  };
  anomalies: Anomaly[];
  incidents: Incident[];
  metrics_before_after: MetricComparison[];
}

export interface MetricComparison {
  metric_name: string;
  before: number[];
  after: number[];
  timestamps: string[];
  change_percentage: number;
  is_anomalous: boolean;
}
