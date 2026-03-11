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

# Create FastAPI app
app = FastAPI(
    title="CloudHelm API",
    description="FinOps + DevOps copilot API for Module A (Core Platform & Cost Radar)",
    version="1.0.0"
)

# Configure CORS
# Support multiple origins for production
allowed_origins = [settings.frontend_origin]

# Add additional origins if specified
if settings.app_env == "production":
    # Allow both with and without trailing slash
    if not settings.frontend_origin.endswith("/"):
        allowed_origins.append(settings.frontend_origin + "/")
    else:
        allowed_origins.append(settings.frontend_origin.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
from backend.routers import auth, cost, overview, releases, resources, health, incidents, assistant
app.include_router(auth.router)
app.include_router(cost.router)
app.include_router(overview.router)
app.include_router(releases.repos_router)
app.include_router(releases.releases_router)
app.include_router(resources.router)
app.include_router(health.router)
app.include_router(incidents.router)
app.include_router(assistant.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "dev"
    )
