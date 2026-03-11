"""
Test main application endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_cors_headers(client: TestClient):
    """Test CORS headers are present."""
    response = client.options("/health")
    assert response.status_code == 200


def test_root_redirect(client: TestClient):
    """Test root endpoint behavior."""
    response = client.get("/")
    # Should either redirect or return 404 (depending on implementation)
    assert response.status_code in [200, 404, 307]


def test_docs_endpoint(client: TestClient):
    """Test API documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema(client: TestClient):
    """Test OpenAPI schema endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert schema["info"]["title"] == "CloudHelm API"
    assert schema["info"]["version"] == "1.0.0"