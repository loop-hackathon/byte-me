from fastapi import APIRouter, HTTPException, Query
import requests
import os

router = APIRouter(prefix="/tracing", tags=["tracing"])

# In a real production setup, this would come from a config/env file.
# For local dev with docker-compose.observability.yml, Tempo is on port 3200.
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")

@router.get("/traces")
async def list_recent_traces(
    limit: int = Query(20, ge=1, le=100),
    project: str = Query(None, description="Project identifier to filter traces by service.namespace")
):
    """
    Proxies a search request to Tempo to get the most recent traces,
    optionally filtered by a specific project name.
    """
    try:
        # Search API in Tempo: /api/search
        params: dict = {"limit": limit}
        if project:
            params["q"] = f'{{ .service.namespace = "{project}" }}'
        else:
            params["q"] = '{ .service.name !~ "cloudhelm-.*" }'
            
        response = requests.get(f"{TEMPO_URL}/api/search", params=params, timeout=2)
        response.raise_for_status()
        data = response.json()
        
        # If no traces found, provide some synthetic ones for demonstration
        if not data.get("traces") or len(data.get("traces")) == 0:
            return get_demo_traces()
            
        return data
    except Exception as e:
        print(f"Tempo unreachable or error: {e}. Returning demo traces.")
        return get_demo_traces()

@router.get("/traces/{trace_id}")
async def get_trace_details(trace_id: str):
    """
    Proxies a request for a specific trace ID to Tempo or returns demo details.
    """
    if trace_id.startswith("demo-"):
        return get_demo_trace_detail(trace_id)
        
    try:
        response = requests.get(f"{TEMPO_URL}/api/traces/{trace_id}", timeout=2)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching trace {trace_id}: {e}")
        # If it's one of our demo IDs or we're in fallback mode
        return get_demo_trace_detail(trace_id)

def get_demo_traces():
    import time
    now_ms = int(time.time() * 1000)
    return {
        "traces": [
            {
                "traceID": "demo-trace-1-latency-spike",
                "durationMs": 1240.5,
                "startTimeUnixNano": str((now_ms - 5000) * 1000000),
                "rootServiceName": "api-gateway",
                "rootTraceName": "POST /api/v1/orders"
            },
            {
                "traceID": "demo-trace-2-cached-hit",
                "durationMs": 45.2,
                "startTimeUnixNano": str((now_ms - 15000) * 1000000),
                "rootServiceName": "api-gateway",
                "rootTraceName": "GET /api/v1/products/123"
            },
            {
                "traceID": "demo-trace-3-db-heavy",
                "durationMs": 850.1,
                "startTimeUnixNano": str((now_ms - 35000) * 1000000),
                "rootServiceName": "inventory-service",
                "rootTraceName": "GET /api/v1/stock/report"
            }
        ],
        "metrics": {"completedJobs": 1, "totalJobs": 1}
    }

def get_demo_trace_detail(trace_id: str):
    import time
    now_ns = int(time.time() * 1000000000)
    
    if "latency-spike" in trace_id:
        return {
            "traceID": trace_id,
            "durationMs": 1240.5,
            "batches": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "frontend-app"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "POST /api/v1/orders", "spanId": "f1", "startTimeUnixNano": str(now_ns - 1240000000), "endTimeUnixNano": str(now_ns)
                    }]}]
                },
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "api-gateway"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "RateLimiter:apply", "spanId": "g1", "parentSpanId": "f1", "startTimeUnixNano": str(now_ns - 1230000000), "endTimeUnixNano": str(now_ns - 1220000000)
                    }, {
                        "name": "AuthService:validate", "spanId": "g2", "parentSpanId": "f1", "startTimeUnixNano": str(now_ns - 1210000000), "endTimeUnixNano": str(now_ns - 1000000000)
                    }]}]
                },
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "order-service"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "OrderService:create", "spanId": "o1", "parentSpanId": "f1", "startTimeUnixNano": str(now_ns - 980000000), "endTimeUnixNano": str(now_ns - 100000000)
                    }, {
                        "name": "INSERT INTO orders", "spanId": "db1", "parentSpanId": "o1", "startTimeUnixNano": str(now_ns - 900000000), "endTimeUnixNano": str(now_ns - 500000000)
                    }, {
                        "name": "PaymentService:authorize", "spanId": "p1", "parentSpanId": "o1", "startTimeUnixNano": str(now_ns - 450000000), "endTimeUnixNano": str(now_ns - 150000000)
                    }]}]
                }
            ]
        }
    
    elif "cached-hit" in trace_id:
        return {
            "traceID": trace_id,
            "durationMs": 45.2,
            "batches": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "frontend-app"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "GET /products/123", "spanId": "f2", "startTimeUnixNano": str(now_ns - 45000000), "endTimeUnixNano": str(now_ns)
                    }]}]
                },
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "api-gateway"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "CacheResolver:hit", "spanId": "g3", "parentSpanId": "f2", "startTimeUnixNano": str(now_ns - 42000000), "endTimeUnixNano": str(now_ns - 2000000)
                    }, {
                        "name": "Redis:GET product_123", "spanId": "db2", "parentSpanId": "g3", "startTimeUnixNano": str(now_ns - 40000000), "endTimeUnixNano": str(now_ns - 35000000)
                    }]}]
                }
            ]
        }
    
    else: # db-heavy
        return {
            "traceID": trace_id,
            "durationMs": 850.1,
            "batches": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "inventory-app"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "GET /report", "spanId": "i1", "startTimeUnixNano": str(now_ns - 850000000), "endTimeUnixNano": str(now_ns)
                    }]}]
                },
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "postgres-db"}}]},
                    "scopeSpans": [{"spans": [{
                        "name": "SELECT * FROM stock_history WHERE date > '2023-01-01' GROUP BY category", "spanId": "db3", "parentSpanId": "i1", "startTimeUnixNano": str(now_ns - 800000000), "endTimeUnixNano": str(now_ns - 50000000)
                    }]}]
                }
            ]
        }


