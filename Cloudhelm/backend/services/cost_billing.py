"""
Cost billing analysis service - ported from feature_2 BillingService.
Provides flexible CSV parsing, anomaly detection, budget simulation,
and Gemini AI-powered deep insights.
"""
import io
import json
import logging
import random
import pandas as pd
import httpx
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger("CostBilling")


class BillingService:
    """Analyzes uploaded cost CSVs with flexible column detection."""

    @staticmethod
    def _detect_columns(df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect service, cost, and date columns from any CSV format.
        Returns mapping: {'service': col_name, 'cost': col_name, 'date': col_name}
        """
        columns = df.columns.tolist()

        service_col = next(
            (c for c in columns if 'service' in c.lower() or 'product' in c.lower()),
            columns[0]
        )
        cost_col = next(
            (c for c in columns if 'cost' in c.lower() or 'amount' in c.lower()),
            columns[-1]
        )
        date_col = next(
            (c for c in columns if 'date' in c.lower() or 'time' in c.lower()),
            None
        )

        return {
            'service': service_col,
            'cost': cost_col,
            'date': date_col,
        }

    @staticmethod
    async def analyze(csv_content: str, gemini_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a cost CSV file - auto-detects columns and computes:
        - Total cost & top service
        - Cost trends (daily by service)
        - Anomaly detection (threshold-based)
        - Budget status (simulated)
        - Gemini AI deep insights (optional)

        Args:
            csv_content: Raw CSV content as string
            gemini_api_key: Optional Gemini API key for AI insights

        Returns:
            Dict with total_cost, top_service, cost_trends, anomalies,
            budget_status, services_count
        """
        # 1. Parse CSV
        df = pd.read_csv(io.StringIO(csv_content))
        col_map = BillingService._detect_columns(df)

        service_col = col_map['service']
        cost_col = col_map['cost']
        date_col = col_map['date']

        # Ensure cost column is numeric
        df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)

        # Handle dates
        if not date_col:
            # Generate synthetic dates if no date column exists
            df['date_internal'] = [
                datetime.now() - timedelta(days=len(df) - i)
                for i in range(len(df))
            ]
            date_col = 'date_internal'
        else:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)

        # 2. Compute cost trends (grouped by day + service)
        trends = df.groupby(
            [pd.Grouper(key=date_col, freq='D'), service_col]
        )[cost_col].sum().reset_index()

        cost_trends = []
        for _, r in trends.iterrows():
            try:
                cost_trends.append({
                    "date": r[date_col].strftime('%Y-%m-%d'),
                    "amount": float(r[cost_col]),
                    "service": str(r[service_col]),
                })
            except Exception:
                continue

        # 3. Python-based anomaly detection (threshold: > 1.3x average)
        py_anomalies = []
        for svc in df[service_col].unique():
            svc_df = df[df[service_col] == svc]
            if len(svc_df) > 1:
                avg = svc_df[cost_col].mean()
                for _, r in svc_df.iterrows():
                    if r[cost_col] > (avg * 1.3) and r[cost_col] > 1:
                        try:
                            anomaly_date = r[date_col].strftime('%Y-%m-%d')
                        except Exception:
                            anomaly_date = str(r[date_col])

                        py_anomalies.append({
                            "date": anomaly_date,
                            "service": str(svc),
                            "amount": float(r[cost_col]),
                            "expected_amount": float(avg),
                            "anomaly_type": "spike",
                            "severity": "high" if r[cost_col] > avg * 1.5 else "medium",
                            "description": f"Spend spike on {svc}: ${r[cost_col]:.2f} (avg: ${avg:.2f})",
                        })

        # 4. Gemini AI deep insights (optional)
        if gemini_api_key:
            try:
                prompt = (
                    f"Analyze these {len(cost_trends)} cost data points for cloud "
                    f"cost anomalies and optimization opportunities. "
                    f"Data: {json.dumps(cost_trends[:50])}. "
                    f"Return JSON: {{'anomalies': [...], 'insights': '...'}}"
                )
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"gemini-1.5-flash:generateContent?key={gemini_api_key}",
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "response_mime_type": "application/json"
                            },
                        },
                    )
                    resp_json = res.json()
                    ai_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                    ai_data = json.loads(ai_text)
                    # Merge AI-detected anomalies
                    ai_anomalies = ai_data.get("anomalies", [])
                    py_anomalies.extend(ai_anomalies)
            except Exception as e:
                logger.warning(f"Gemini AI analysis failed: {e}")

        # 5. Generate budget status (simulated from actual spend)
        budget_status = []
        for svc in df[service_col].unique():
            svc_df = df[df[service_col] == svc]
            actual_spend = float(svc_df[cost_col].sum())
            if actual_spend <= 0:
                continue

            # Simulate a realistic budget with variance
            variance_factor = random.uniform(-0.2, 0.2)
            allocated_budget = actual_spend / (1 + variance_factor)
            variance_percent = ((actual_spend - allocated_budget) / allocated_budget) * 100

            if variance_percent < -5:
                status = "under_budget"
            elif variance_percent > 5:
                status = "over_budget"
            else:
                status = "on_track"

            budget_status.append({
                "service": str(svc),
                "actual_spend": actual_spend,
                "allocated_budget": round(allocated_budget, 2),
                "variance_percent": round(variance_percent, 2),
                "status": status,
            })

        # 6. Build final response
        top_service = str(df.groupby(service_col)[cost_col].sum().idxmax())
        total_cost = float(df[cost_col].sum())

        # Detect biggest cost spike for banner
        critical_anomaly = next(
            (a for a in sorted(py_anomalies, key=lambda x: x['amount'], reverse=True)
             if a['severity'] in ('critical', 'high')),
            None
        )

        return {
            "total_cost": total_cost,
            "top_service": top_service,
            "cost_trends": cost_trends,
            "anomalies": py_anomalies[:20],
            "budget_status": budget_status,
            "services_count": int(df[service_col].nunique()),
            # Spike banner fields (mirrors feature_2 response)
            "cost_spike_detected": critical_anomaly is not None,
            "cost_spike_service": critical_anomaly["service"] if critical_anomaly else None,
            "cost_spike_amount": critical_anomaly["amount"] if critical_anomaly else 0,
        }

    @staticmethod
    def convert_to_cloudhelm_format(
        analysis: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Convert BillingService analysis results to the format expected
        by CloudHelm frontend components (CostSummaryResponse, etc).

        This maps the feature_2 analysis output to the CloudHelm schema
        so the existing UI renders correctly.
        """
        # Convert cost_trends to CostSummaryResponse format
        # Group trends by service -> series
        series_map: Dict[str, List[Dict[str, Any]]] = {}
        for trend in analysis.get("cost_trends", []):
            svc = trend.get("service", "unknown")
            if svc not in series_map:
                series_map[svc] = []
            series_map[svc].append({
                "date": trend["date"],
                "total_cost": trend["amount"],
            })

        series = [
            {"key": key, "points": sorted(points, key=lambda p: p["date"])}
            for key, points in series_map.items()
        ]

        # Determine date range from trends
        all_dates = [t["date"] for t in analysis.get("cost_trends", [])]
        from_date = min(all_dates) if all_dates else str(date.today())
        to_date = max(all_dates) if all_dates else str(date.today())

        cost_summary = {
            "from": from_date,
            "to": to_date,
            "group_by": "service",
            "series": series,
            "total_cost": analysis.get("total_cost", 0),
        }

        # Convert anomalies to CostAnomaly format
        anomalies = []
        for i, a in enumerate(analysis.get("anomalies", [])):
            anomalies.append({
                "id": i + 1,
                "ts_date": a.get("date", str(date.today())),
                "cloud": "aws",
                "team": None,
                "service": a.get("service"),
                "region": None,
                "env": None,
                "actual_cost": a.get("amount", 0),
                "expected_cost": a.get("expected_amount", 0),
                "anomaly_score": 1.0,
                "direction": a.get("anomaly_type", "spike"),
                "severity": a.get("severity", "medium"),
            })

        # Convert budget_status to BudgetStatus format
        budgets = []
        for b in analysis.get("budget_status", []):
            projected = b["actual_spend"]
            monthly_budget = b["allocated_budget"]

            if b["status"] == "under_budget":
                status = "UNDER"
            elif b["status"] == "over_budget":
                status = "OVER"
            else:
                status = "AT_RISK"

            budgets.append({
                "team": b["service"],  # Use service as team for display
                "service": b["service"],
                "monthly_budget": monthly_budget,
                "mtd_cost": b["actual_spend"],
                "projected_cost": projected,
                "status": status,
                "currency": "USD",
            })

        return {
            "cost_summary": cost_summary,
            "anomalies": anomalies,
            "budgets": budgets,
        }

    @staticmethod
    def get_cost_by_service(db: Session, user_id: int):
        """Get aggregate cost by service from database."""
        from backend.models.cost import CostAggregate
        from sqlalchemy import func
        
        results = db.query(
            CostAggregate.service,
            func.sum(CostAggregate.total_cost).label('amount')
        ).filter(
            CostAggregate.user_id == user_id
        ).group_by(
            CostAggregate.service
        ).all()
        
        return results

cost_billing_service = BillingService()
