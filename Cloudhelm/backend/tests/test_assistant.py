"""
Test CloudHelm Assistant API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


class TestAssistantAPI:
    """Test assistant API endpoints."""

    def test_assistant_status_enabled(self, client: TestClient):
        """Test assistant status when Mistral is enabled."""
        with patch('services.mistral_service.mistral_service') as mock_service:
            mock_service.enabled = True
            mock_service.model = "mistral-large-latest"
            
            response = client.get("/api/assistant/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["enabled"] is True
            assert data["model"] == "mistral-large-latest"
            assert data["service"] == "Mistral AI"

    def test_assistant_status_disabled(self, client: TestClient):
        """Test assistant status when Mistral is disabled."""
        with patch('services.mistral_service.mistral_service') as mock_service:
            mock_service.enabled = False
            mock_service.model = None
            
            response = client.get("/api/assistant/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["enabled"] is False
            assert data["model"] is None
            assert data["service"] == "Mistral AI"

    def test_query_assistant_without_auth(self, client: TestClient):
        """Test querying assistant without authentication."""
        response = client.post("/api/assistant/query", json={
            "query": "/help",
            "context_type": "general"
        })
        assert response.status_code == 401

    @patch('services.mistral_service.mistral_service')
    def test_query_assistant_service_disabled(self, mock_service, client: TestClient):
        """Test querying assistant when service is disabled."""
        mock_service.enabled = False
        
        # Mock authentication (you'll need to implement proper auth mocking)
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"id": 1, "username": "testuser"}
            
            response = client.post("/api/assistant/query", json={
                "query": "/help",
                "context_type": "general"
            })
            assert response.status_code == 503
            assert "not available" in response.json()["detail"]

    @patch('services.mistral_service.mistral_service')
    async def test_query_assistant_general_context(self, mock_service, client: TestClient):
        """Test querying assistant with general context."""
        mock_service.enabled = True
        mock_service.analyze_code = AsyncMock(return_value="AI response for general query")
        
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"id": 1, "username": "testuser"}
            
            response = client.post("/api/assistant/query", json={
                "repository_name": "test-repo",
                "query": "Analyze this code",
                "context_type": "general"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "AI response for general query"
            assert data["repository_name"] == "test-repo"

    @patch('services.mistral_service.mistral_service')
    async def test_query_assistant_incident_context(self, mock_service, client: TestClient):
        """Test querying assistant with incident context."""
        mock_service.enabled = True
        mock_service.suggest_incident_solution = AsyncMock(return_value="AI incident solution")
        
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"id": 1, "username": "testuser"}
            
            response = client.post("/api/assistant/query", json={
                "repository_name": "test-repo",
                "query": "Server is down",
                "context_type": "incident",
                "code_snippet": "Error logs here"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "AI incident solution"

    @patch('services.mistral_service.mistral_service')
    async def test_query_assistant_security_context(self, mock_service, client: TestClient):
        """Test querying assistant with security context."""
        mock_service.enabled = True
        mock_service.review_security = AsyncMock(return_value="Security review results")
        
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"id": 1, "username": "testuser"}
            
            response = client.post("/api/assistant/query", json={
                "repository_name": "test-repo",
                "query": "Review security",
                "context_type": "security",
                "code_snippet": "function authenticate() { ... }"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Security review results"

    @patch('services.mistral_service.mistral_service')
    async def test_query_assistant_cli_command(self, mock_service, client: TestClient):
        """Test querying assistant with CLI command."""
        mock_service.enabled = True
        mock_service.analyze_code = AsyncMock(return_value="CLI command executed successfully")
        
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"id": 1, "username": "testuser"}
            
            response = client.post("/api/assistant/query", json={
                "repository_name": "test-repo",
                "query": "/test",
                "context_type": "general"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "CLI command executed successfully"

    @patch('services.mistral_service.mistral_service')
    async def test_query_assistant_error_handling(self, mock_service, client: TestClient):
        """Test assistant error handling."""
        mock_service.enabled = True
        mock_service.analyze_code = AsyncMock(return_value=None)  # Simulate failure
        
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"id": 1, "username": "testuser"}
            
            response = client.post("/api/assistant/query", json={
                "repository_name": "test-repo",
                "query": "Test query",
                "context_type": "general"
            })
            
            assert response.status_code == 500
            assert "Failed to generate response" in response.json()["detail"]