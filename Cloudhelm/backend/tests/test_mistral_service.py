"""
Test Mistral AI service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import re

from services.mistral_service import MistralService


class TestMistralService:
    """Test Mistral AI service functionality."""

    def test_init_with_api_key(self):
        """Test service initialization with API key."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            assert service.enabled is True
            assert service.api_key == "test-api-key"
            assert service.model == "mistral-large-latest"

    def test_init_without_api_key(self):
        """Test service initialization without API key."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = None
            
            service = MistralService()
            assert service.enabled is False
            assert service.api_key is None

    @pytest.mark.asyncio
    async def test_analyze_code_disabled(self):
        """Test analyze_code when service is disabled."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = None
            
            service = MistralService()
            result = await service.analyze_code("test-repo", question="Test question")
            assert result is None

    @pytest.mark.asyncio
    async def test_analyze_code_success(self):
        """Test successful code analysis."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch.object(service, '_call_mistral_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = "Analysis result"
                
                result = await service.analyze_code(
                    repository_name="test-repo",
                    code_snippet="def hello(): pass",
                    question="What does this do?"
                )
                
                assert result == "Analysis result"
                mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_cli_command_help(self):
        """Test /help CLI command."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            result = await service.analyze_code("test-repo", question="/help")
            
            assert result is not None
            assert "CLI Commands" in result
            assert "/test" in result
            assert "/lint" in result
            assert "/errors" in result

    @pytest.mark.asyncio
    async def test_cli_command_test(self):
        """Test /test CLI command."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch('asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = MagicMock()
                mock_process.communicate.return_value = (b"Tests passed", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                with patch('asyncio.wait_for') as mock_wait:
                    mock_wait.return_value = (b"Tests passed", b"")
                    
                    result = await service.analyze_code("test-repo", question="/test")
                    
                    assert result is not None
                    assert "Running Tests" in result
                    assert "Tests passed" in result

    @pytest.mark.asyncio
    async def test_cli_command_lint(self):
        """Test /lint CLI command."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch('asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = MagicMock()
                mock_process.communicate.return_value = (b"No linting errors", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                with patch('asyncio.wait_for') as mock_wait:
                    mock_wait.return_value = (b"No linting errors", b"")
                    
                    result = await service.analyze_code("test-repo", question="/lint")
                    
                    assert result is not None
                    assert "Running Linter" in result

    @pytest.mark.asyncio
    async def test_cli_command_errors(self):
        """Test /errors CLI command."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch('asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = MagicMock()
                mock_process.communicate.return_value = (b"", b"syntax error")
                mock_process.returncode = 1
                mock_subprocess.return_value = mock_process
                
                with patch('asyncio.wait_for') as mock_wait:
                    mock_wait.return_value = (b"", b"syntax error")
                    
                    result = await service.analyze_code("test-repo", question="/errors")
                    
                    assert result is not None
                    assert "Finding Errors" in result

    @pytest.mark.asyncio
    async def test_cli_command_run_safe(self):
        """Test /run CLI command with safe command."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch('asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = MagicMock()
                mock_process.communicate.return_value = (b"git status output", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                with patch('asyncio.wait_for') as mock_wait:
                    mock_wait.return_value = (b"git status output", b"")
                    
                    result = await service.analyze_code("test-repo", question="/run git status")
                    
                    assert result is not None
                    assert "Command Executed" in result
                    assert "git status" in result

    @pytest.mark.asyncio
    async def test_cli_command_run_unsafe(self):
        """Test /run CLI command with unsafe command."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            result = await service.analyze_code("test-repo", question="/run rm -rf /")
            
            assert result is not None
            assert "Command Not Allowed" in result
            assert "security reasons" in result

    @pytest.mark.asyncio
    async def test_suggest_incident_solution(self):
        """Test incident solution suggestion."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch.object(service, '_call_mistral_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = "Incident solution"
                
                result = await service.suggest_incident_solution(
                    repository_name="test-repo",
                    incident_description="Server is down",
                    error_logs="Connection refused"
                )
                
                assert result == "Incident solution"
                mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_security(self):
        """Test security review."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            with patch.object(service, '_call_mistral_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = "Security review results"
                
                result = await service.review_security(
                    repository_name="test-repo",
                    code_snippet="function authenticate() { ... }"
                )
                
                assert result == "Security review results"
                mock_api.assert_called_once()

    def test_command_patterns(self):
        """Test CLI command regex patterns."""
        with patch('services.mistral_service.settings') as mock_settings:
            mock_settings.mistral_api_key = "test-api-key"
            
            service = MistralService()
            
            # Test patterns
            patterns = service.cli_commands.keys()
            
            # Test /help pattern
            help_pattern = r'^/help$'
            assert any(re.match(help_pattern, "/help") for pattern in patterns if pattern == help_pattern)
            
            # Test /test pattern
            test_pattern = r'^/test\s*(.*)$'
            assert any(re.match(test_pattern, "/test") for pattern in patterns if pattern == test_pattern)
            assert any(re.match(test_pattern, "/test backend/") for pattern in patterns if pattern == test_pattern)
            
            # Test /run pattern
            run_pattern = r'^/run\s+(.+)$'
            assert any(re.match(run_pattern, "/run git status") for pattern in patterns if pattern == run_pattern)