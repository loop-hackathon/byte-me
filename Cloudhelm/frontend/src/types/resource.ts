/**
 * Type definitions for Resource Efficiency feature.
 * Adapted from Loop_ResourceDashboard for CloudHelm.
 */

export interface Resource {
  id: string;
  name: string;
  resource_type: string;
  team: string;
  environment: string;
  waste_score: number;
  avg_cpu?: number;
  avg_memory?: number;
  created_at: string;
}

export interface ResourceMetric {
  id: number;
  resource_id: string;
  timestamp: string;
  cpu_utilization: number;
  memory_utilization: number;
  disk_io?: number;
  network_io?: number;
}

export interface Recommendation {
  id: number;
  resource_id: string;
  resource_name?: string;
  recommendation_type: 'rightsizing' | 'schedule';
  description: string;
  potential_savings: number;
  suggested_action: string;
  confidence: number;
  created_at: string;
}

export interface DashboardStats {
  average_waste_score: number;
  underutilized_vms: number;
  potential_savings: number;
  schedulable_resources: number;
}

export interface WasteScoreData {
  date: string;
  score: number;
}

export interface UnderutilizedVM {
  id: string;
  name: string;
  cpu: number;
  memory: number;
  disk: number;
  environment: string;
  team: string;
  monthly_underspend: number;
  waste_score: number;
}

export interface RightsizingSuggestion {
  id: number;
  resource_id: string;
  resource_name: string;
  current_type: string;
  recommended_type: string;
  monthly_savings: number;
  confidence: number;
  reason: string;
}

export interface ScheduleRecommendation {
  id: number;
  resource_id: string;
  resource_name: string;
  environment: string;
  team: string;
  schedule: string;
  idle_percentage: number;
  monthly_savings: number;
  hourly_pattern?: number[];
}

export interface ResourceFilters {
  team?: string;
  environment?: string;
  search?: string;
  min_waste_score?: number;
}

export interface RecommendationFilters {
  recommendation_type?: 'rightsizing' | 'schedule';
  team?: string;
  environment?: string;
}
