export interface CostSummaryPoint {
  date: string;
  total_cost: number;
}

export interface CostSummarySeries {
  key: string;
  points: CostSummaryPoint[];
}

export interface CostSummaryResponse {
  from: string;
  to: string;
  group_by: string;
  series: CostSummarySeries[];
  total_cost: number;
}

export interface CostAnomaly {
  id: number;
  ts_date: string;
  cloud: string;
  team: string | null;
  service: string | null;
  region: string | null;
  env: string | null;
  actual_cost: number;
  expected_cost: number;
  anomaly_score: number;
  direction: 'spike' | 'drop';
  severity: 'low' | 'medium' | 'high';
}

export interface BudgetStatus {
  team: string;
  service: string | null;
  monthly_budget: number;
  mtd_cost: number;
  projected_cost: number;
  status: 'UNDER' | 'AT_RISK' | 'OVER';
  currency: string;
}

export interface UploadResponse {
  rows_ingested: number;
  start_date: string;
  end_date: string;
  total_cost: number;
  cloud: string;
}

export interface ForecastPoint {
  date: string;
  projected_cost: number;
}

export interface ForecastResponse {
  key: string;
  forecast_points: ForecastPoint[];
}
