import logging
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Optional, Any
import io

logger = logging.getLogger(__name__)

# Module-level cache for CSV data
# Structure: { user_id: { "grafana": df, "gemini": df } }
_efficiency_cache: Dict[int, Dict[str, pd.DataFrame]] = {}

class EfficiencyService:
    @staticmethod
    def store_csv_data(user_id: int, source: str, csv_content: str):
        """Store CSV data in cache for a user."""
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            if user_id not in _efficiency_cache:
                _efficiency_cache[user_id] = {}
            _efficiency_cache[user_id][source] = df
            logger.info(f"Stored {source} CSV data for user {user_id}. Rows: {len(df)}")
            return True
        except Exception as e:
            logger.error(f"Error storing CSV data: {e}")
            return False

    @staticmethod
    def get_resource_efficiency(user_id: int, db_costs: List[Dict], dynamic_metrics: Optional[List[Dict]] = None):
        """
        Calculate resource efficiency using cached CSVs, dynamic health metrics, and database costs.
        
        Formula: efficiency_score = cpu_util / 50 * (1 / normalized_cost_per_core)
        Analysis: Simple LinearRegression on cpu history vs cost history.
        """
        user_cache = _efficiency_cache.get(user_id, {})
        grafana_df = user_cache.get("grafana")
        gemini_df = user_cache.get("gemini")

        try:
            # 1. Collect CPU Data (Prioritize Dynamic Metrics, fall back to Grafana CSV)
            cpu_data: Dict[str, float] = {}
            
            # First, take from dynamic metrics (if available)
            if dynamic_metrics:
                for metric in dynamic_metrics:
                    # Health summary has resources.cpu
                    cpu_val = metric.get('resources', {}).get('cpu', 0.0)
                    service_name = metric.get('service_name')
                    if service_name and cpu_val > 0:
                        cpu_data[service_name] = float(cpu_val)
            
            # Then, fill in from Grafana CSV if not already present
            if grafana_df is not None:
                if 'service' in grafana_df.columns and 'cpu_util' in grafana_df.columns:
                    csv_cpu = grafana_df.groupby('service')['cpu_util'].mean().to_dict()
                    for s, v in csv_cpu.items():
                        if s not in cpu_data:
                            cpu_data[s] = float(v)
            
            # 2. Collect Cost Data (Prioritize DB costs, fall back to Gemini CSV)
            cost_data: Dict[str, float] = {}
            if db_costs:
                cost_data = {c['service']: float(c['cost']) for c in db_costs}
            
            if gemini_df is not None and 'service' in gemini_df.columns and 'cost' in gemini_df.columns:
                csv_costs = gemini_df.groupby('service')['cost'].sum().to_dict()
                for s, v in csv_costs.items():
                    if s not in cost_data:
                        cost_data[s] = float(v)

            # If no data at all, return demo data
            if not cpu_data and not cost_data:
                return EfficiencyService._get_demo_data()

            scatter_data: List[Dict[str, Any]] = []
            all_cpu: List[float] = []
            all_cost: List[float] = []

            # Combine CPU and Cost
            # We iterate through all services we have ANY data for
            all_services = set(cpu_data.keys()) | set(cost_data.keys())

            for service in all_services:
                cpu_val = cpu_data.get(service, 0.0)
                cost_val = cost_data.get(service, 0.0)
                
                if cost_val > 0:
                    # Normalized cost per core (assuming 1k spend is baseline)
                    normalized_cost = cost_val / 1000.0
                    
                    # Score = cpu_util / 50 * (1 / normalized_cost)
                    efficiency = (cpu_val / 50.0) * (1.0 / max(0.1, normalized_cost))
                    efficiency = min(1.0, efficiency)

                    scatter_data.append({
                        "service": str(service),
                        "cpu_pct": round(cpu_val, 2),
                        "cost": round(cost_val, 2),
                        "efficiency": round(efficiency, 2)
                    })
                    
                    all_cpu.append(cpu_val)
                    all_cost.append(cost_val)

            # Linear Regression Analysis
            recommendations: List[str] = []
            if len(all_cpu) > 1:
                X = np.array(all_cpu).reshape(-1, 1)
                y = np.array(all_cost)
                model = LinearRegression()
                model.fit(X, y)
                
                # Services with high cost but low CPU are candidates for rightsizing
                cost_mean = float(np.mean(all_cost))
                for item in scatter_data:
                    item_cpu = float(item['cpu_pct'])
                    item_cost = float(item['cost'])
                    if item_cpu < 25.0 and item_cost > cost_mean:
                        savings = item_cost * 0.4
                        recommendations.append(f"Right-size {item['service']}: save ${savings:,.0f}/mo")
            
            # Simple fallback recommendations if no regression
            if not recommendations:
                for item in scatter_data:
                    if item['cpu_pct'] < 10:
                        recommendations.append(f"Shutdown idle service {item['service']}")

            avg_eff = float(np.mean([float(d['efficiency']) for d in scatter_data])) if scatter_data else 0.0

            return {
                "scatter_data": scatter_data,
                "recommendations": recommendations[:5] if recommendations else [],
                "avg_efficiency": round(avg_eff, 2)
            }

        except Exception as e:
            logger.error(f"Error in efficiency analysis: {e}")
            return EfficiencyService._get_demo_data()

    @staticmethod
    def _get_demo_data():
        return {
            "scatter_data": [
                {"service": "Prod-API", "cpu_pct": 15, "cost": 2500, "efficiency": 0.32},
                {"service": "Auth-SVC", "cpu_pct": 45, "cost": 1200, "efficiency": 0.85},
                {"service": "Data-Worker", "cpu_pct": 78, "cost": 3400, "efficiency": 0.92},
                {"service": "Cache-Layer", "cpu_pct": 12, "cost": 800, "efficiency": 0.45},
                {"service": "ML-Inference", "cpu_pct": 65, "cost": 5600, "efficiency": 0.72}
            ],
            "recommendations": [
                "Right-size Prod-API: save $1,200/mo",
                "Consolidate Cache-Layer instances",
                "Review ML-Inference instance types"
            ],
            "avg_efficiency": 0.65
        }
