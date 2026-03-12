"""
Main FastAPI application entry point.
"""
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from backend.core.config import settings

# ── Distributed Tracing (OpenTelemetry) ─────────────────────────────────────
# Must be initialised BEFORE the app is created and BEFORE any routers are
# imported so that all library instrumentors can register their hooks in time.
try:
    from backend.core.db import engine as db_engine
    from backend.core.tracing import setup_tracing
    setup_tracing(sqlalchemy_engine=db_engine)
except Exception:
    pass  # Tracing is optional — app works without it
# ────────────────────────────────────────────────────────────────────────────

# Create FastAPI app
app = FastAPI(
    title="CloudHelm API",
    description="FinOps + DevOps copilot API for Module A (Core Platform & Cost Radar)",
    version="1.0.0"
)

# ── Auto-instrument every FastAPI endpoint ──────────────────────────────────
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
except ImportError:
    pass  # OTel not installed — skip instrumentation
# ────────────────────────────────────────────────────────────────────────────

# Configure CORS
# Hardcoded for dev environment as requested to fix "Failed to fetch" issues
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    settings.frontend_origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.app_env}

# Include routers
from backend.routers import auth, cost, overview, releases, resources, health, incidents, assistant, efficiency, tracing
app.include_router(auth.router)
app.include_router(cost.router)
app.include_router(overview.router)
app.include_router(releases.repos_router)
app.include_router(releases.releases_router)
app.include_router(resources.router)
app.include_router(health.router)
app.include_router(incidents.router)
app.include_router(assistant.router)
app.include_router(efficiency.router)
app.include_router(tracing.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "dev"
    )
