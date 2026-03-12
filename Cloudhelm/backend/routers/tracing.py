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
            # Filter by OTLP resource attribute: service.namespace using TraceQL
            params["q"] = f'{{ .service.namespace = "{project}" }}'
        else:
            # Exclude internal CloudHelm traces when no project is specified
            params["q"] = '{ .service.name !~ "cloudhelm-.*" }'
            
        response = requests.get(f"{TEMPO_URL}/api/search", params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Tempo: {e}")
        raise HTTPException(status_code=502, detail="Error fetching traces from Tempo")

@router.get("/traces/{trace_id}")
async def get_trace_details(trace_id: str):
    """
    Proxies a request for a specific trace ID to Tempo.
    Returns the full OTLP JSON of the trace.
    """
    try:
        # Trace details API in Tempo: /api/traces/{id}
        # Note: Tempo returns traces in OTLP format as JSON.
        response = requests.get(f"{TEMPO_URL}/api/traces/{trace_id}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trace {trace_id}: {e}")
        if hasattr(response, 'status_code') and response.status_code == 404:
             raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        raise HTTPException(status_code=502, detail="Error fetching trace details from Tempo")
