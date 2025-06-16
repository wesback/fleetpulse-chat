"""Test MCP error handling and diagnostic capabilities."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from core.mcp_client import FleetPulseMCPClient, MCPToolResult, ErrorType
from utils.mcp_diagnostics import MCPDiagnosticRunner, DiagnosticResult


class TestMCPErrorHandling:
    """Test comprehensive error handling for MCP tools."""
    
    @pytest.fixture
    def mcp_client(self):
        """Create MCP client for testing."""
        with patch('core.mcp_client.get_settings') as mock_settings:
            mock_settings.return_value.fleetpulse_api_url = "http://localhost:8000"
            return FleetPulseMCPClient()
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, mcp_client):
        """Test network error classification and response."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.ConnectError("Connection refused")
            
            result = await mcp_client.execute_tool("get_fleet_status", {})
            
            assert not result.success
            assert result.error_type == ErrorType.NETWORK_ERROR
            assert "connect to FleetPulse backend" in result.error
            assert "recovery_actions" in result.diagnostics
            assert any("backend service" in action.lower() for action in result.diagnostics["recovery_actions"])
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, mcp_client):
        """Test timeout error classification and response."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Request timed out")
            
            result = await mcp_client.execute_tool("get_update_history", {"hostname": "test-host"})
            assert not result.success
            assert result.error_type == ErrorType.TIMEOUT_ERROR
            assert "timed out" in result.error
            assert result.diagnostics
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, mcp_client):
        """Test authentication error classification."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Unauthorized", request=None, response=mock_response)
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await mcp_client.execute_tool("get_host_details", {"hostname": "test-host"})
            
            assert not result.success
            assert result.error_type == ErrorType.AUTHENTICATION_ERROR
            assert "authentication" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_database_error_detection(self, mcp_client):
        """Test database error detection and handling."""
        with patch('httpx.AsyncClient') as mock_client:
            # Simulate database-related error
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("SQLite database is locked")
            
            result = await mcp_client.execute_tool("get_update_history", {"hostname": "test-host"})
            
            assert not result.success
            assert result.error_type == ErrorType.DATABASE_ERROR
            assert "database" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_tool_not_found_error(self, mcp_client):
        """Test handling of non-existent tools."""
        result = await mcp_client.execute_tool("non_existent_tool", {})
        
        assert not result.success
        assert result.error_type == ErrorType.TOOL_NOT_FOUND
        assert "not found" in result.error
        assert "Available tools:" in result.error
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, mcp_client):
        """Test parameter validation error handling."""
        result = await mcp_client.execute_tool("get_host_details", {})  # Missing required hostname
        
        assert not result.success
        assert result.error_type == ErrorType.VALIDATION_ERROR
        assert "required" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_error_count_tracking(self, mcp_client):
        """Test that error counts are properly tracked."""
        initial_count = mcp_client._error_count
        
        # Simulate multiple errors
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.ConnectError("Connection refused")
            
            await mcp_client.execute_tool("get_fleet_status", {})
            await mcp_client.execute_tool("get_host_details", {"hostname": "test"})
        
        assert mcp_client._error_count > initial_count
    
    @pytest.mark.asyncio
    async def test_diagnostics_update(self, mcp_client):
        """Test that diagnostics are properly updated."""
        diagnostics = await mcp_client.get_diagnostics()
        
        assert diagnostics is not None
        assert hasattr(diagnostics, 'backend_status')
        assert hasattr(diagnostics, 'error_count')
        assert hasattr(diagnostics, 'network_connectivity')


class TestMCPDiagnostics:
    """Test MCP diagnostic capabilities."""
    
    @pytest.fixture
    def diagnostic_runner(self):
        """Create diagnostic runner for testing."""
        with patch('utils.mcp_diagnostics.get_settings') as mock_settings:
            mock_settings.return_value.fleetpulse_api_url = "http://localhost:8000"
            return MCPDiagnosticRunner()
    
    @pytest.mark.asyncio
    async def test_backend_connectivity_check_healthy(self, diagnostic_runner):
        """Test backend connectivity check when healthy."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await diagnostic_runner._check_backend_connectivity()
            
            assert result.name == "Backend Connectivity"
            assert result.status == "healthy"
            assert "responding normally" in result.message
    
    @pytest.mark.asyncio
    async def test_backend_connectivity_check_unhealthy(self, diagnostic_runner):
        """Test backend connectivity check when unhealthy."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.ConnectError("Connection refused")
            
            result = await diagnostic_runner._check_backend_connectivity()
            
            assert result.name == "Backend Connectivity"
            assert result.status == "error"
            assert "Cannot connect" in result.message
            assert result.recovery_actions is not None
    
    @pytest.mark.asyncio
    async def test_database_access_check(self, diagnostic_runner):
        """Test database access check."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"hostname": "test"}]
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await diagnostic_runner._check_database_access()
            
            assert result.name == "Database Access"
            assert result.status == "healthy"
            assert "accessible" in result.message
    
    @pytest.mark.asyncio
    async def test_api_endpoints_check(self, diagnostic_runner):
        """Test API endpoints check."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            results = await diagnostic_runner._check_api_endpoints()
            
            assert len(results) > 0
            assert all(isinstance(r, DiagnosticResult) for r in results)
            assert all(r.name.startswith("API Endpoint") for r in results)
    
    @pytest.mark.asyncio
    async def test_network_connectivity_check(self, diagnostic_runner):
        """Test network connectivity check."""
        with patch('asyncio.open_connection') as mock_connection:
            mock_writer = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_connection.return_value = (None, mock_writer)
            
            result = await diagnostic_runner._check_network_connectivity()
            
            assert result.name == "Network Connectivity"
            assert result.status == "healthy"
            assert "successful" in result.message
    
    @pytest.mark.asyncio
    async def test_full_diagnostics_run(self, diagnostic_runner):
        """Test full diagnostic run."""
        with patch.multiple(
            diagnostic_runner,
            _check_backend_connectivity=AsyncMock(return_value=DiagnosticResult("Backend", "healthy", "OK")),
            _check_api_endpoints=AsyncMock(return_value=[DiagnosticResult("API", "healthy", "OK")]),
            _check_database_access=AsyncMock(return_value=DiagnosticResult("Database", "healthy", "OK")),
            _check_network_connectivity=AsyncMock(return_value=DiagnosticResult("Network", "healthy", "OK")),
            _check_system_resources=AsyncMock(return_value=DiagnosticResult("Resources", "healthy", "OK")),
            _check_mcp_service_health=AsyncMock(return_value=DiagnosticResult("MCP", "healthy", "OK"))
        ):
            results = await diagnostic_runner.run_full_diagnostics()
            
            assert len(results) >= 5  # At least 5 diagnostic checks
            assert all(isinstance(r, DiagnosticResult) for r in results)


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_automatic_retry_on_transient_error(self, mcp_client):
        """Test automatic retry logic for transient errors."""
        # This would test retry logic if implemented
        pass
    
    @pytest.mark.asyncio
    async def test_fallback_to_cached_data(self, mcp_client):
        """Test fallback to cached data when tools fail."""
        # This would test caching mechanisms if implemented
        pass
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, mcp_client):
        """Test circuit breaker pattern for failing services."""
        # This would test circuit breaker implementation if added
        pass


class TestDiagnosticReporting:
    """Test diagnostic reporting functionality."""
    
    def test_diagnostic_report_generation(self):
        """Test generation of diagnostic reports."""
        from utils.mcp_diagnostics import generate_diagnostic_report
        
        results = [
            DiagnosticResult("Test1", "healthy", "All good"),
            DiagnosticResult("Test2", "error", "Something wrong", recovery_actions=["Fix it"]),
            DiagnosticResult("Test3", "warning", "Be careful")
        ]
        
        report = generate_diagnostic_report(results)
        
        assert "FleetPulse MCP Diagnostic Report" in report
        assert "1 healthy, 1 warnings, 1 errors" in report
        assert "Test1" in report
        assert "Test2" in report
        assert "Test3" in report
        assert "Fix it" in report
    
    def test_error_classification_accuracy(self):
        """Test accuracy of error classification."""
        from core.mcp_client import FleetPulseMCPClient
        
        with patch('core.mcp_client.get_settings') as mock_settings:
            mock_settings.return_value.fleetpulse_api_url = "http://localhost:8000"
            client = FleetPulseMCPClient()
            
            # Test various error types
            timeout_error = client._classify_error(httpx.TimeoutException("timeout"))
            assert timeout_error == ErrorType.TIMEOUT_ERROR
            
            connect_error = client._classify_error(httpx.ConnectError("connection failed"))
            assert connect_error == ErrorType.NETWORK_ERROR
            
            database_error = client._classify_error(Exception("SQLite database locked"))
            assert database_error == ErrorType.DATABASE_ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
