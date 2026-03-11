export interface Incident {
  id: number;
  incident_id: string;
  title: string;
  description?: string;
  service?: string;
  env?: string;
  team?: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  resolved_at?: string;
  anomalies?: string;
  recent_releases?: string;
  metrics_summary?: string;
  cost_changes?: string;
  ai_summary?: string;
  summary_generated_at?: string;
}

export interface IncidentCreate {
  incident_id: string;
  title: string;
  description?: string;
  service?: string;
  env?: string;
  team?: string;
  status: string;
  severity: string;
  anomalies?: string;
  recent_releases?: string;
  metrics_summary?: string;
  cost_changes?: string;
}

export interface IncidentUpdate {
  title?: string;
  description?: string;
  status?: string;
  severity?: string;
  service?: string;
  env?: string;
  team?: string;
  anomalies?: string;
  recent_releases?: string;
  metrics_summary?: string;
  cost_changes?: string;
  resolved_at?: string;
}

export interface GenerateSummaryResponse {
  incident_id: string;
  summary: string;
  generated_at: string;
  request_id: string;
}
