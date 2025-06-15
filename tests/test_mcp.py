"""Tests for MCP Client functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from core.mcp_client import FleetPulseMCPClient, MCPTool, MCPToolResult


@pytest.fixture
def mcp_client():
    """Create MCP client for testing."""
    with patch('core.mcp_client.get_settings') as mock_settings:
        mock_settings.return_value.fleetpulse_api_url = "http://test-api:8000"
        return FleetPulseMCPClient()


class TestMCPTool:
    """Test MCP tool dataclass."""
    
    def test_mcp_tool_creation(self):
        """Test creating an MCP tool."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            parameters={"param1": {"type": "string"}}
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert "param1" in tool.parameters


class TestMCPToolResult:
    """Test MCP tool result dataclass."""
    
    def test_successful_result(self):
        """Test creating a successful result."""
        result = MCPToolResult(success=True, data={"status": "ok"})
        assert result.success is True
        assert result.data == {"status": "ok"}
        assert result.error is None
    
    def test_error_result(self):
        """Test creating an error result."""
        result = MCPToolResult(success=False, data=None, error="Something went wrong")
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"


class TestFleetPulseMCPClient:
    """Test FleetPulse MCP client functionality."""
    
    def test_initialization(self, mcp_client):
        """Test MCP client initialization."""
        assert mcp_client is not None
        assert hasattr(mcp_client, 'tools')
        assert hasattr(mcp_client, 'base_url')
        assert mcp_client.base_url == "http://test-api:8000"
    
    def test_tool_registration(self, mcp_client):
        """Test that tools are properly registered."""
        tools = mcp_client.get_available_tools()
        assert len(tools) > 0
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "get_fleet_status",
            "get_host_details", 
            "get_update_history",
            "get_pending_updates",
            "schedule_updates",
            "generate_fleet_report",
            "get_system_metrics",
            "check_package_info"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_get_tool(self, mcp_client):
        """Test getting a specific tool."""
        tool = mcp_client.get_tool("get_fleet_status")
        assert tool is not None
        assert tool.name == "get_fleet_status"
        
        # Test non-existent tool
        non_existent = mcp_client.get_tool("non_existent_tool")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, mcp_client):
        """Test executing an unknown tool."""
        result = await mcp_client.execute_tool("unknown_tool", {})
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio 
    async def test_get_fleet_status_success(self, mcp_client):
        """Test successful fleet status retrieval."""
        mock_response_data = {
            "total_hosts": 10,
            "online_hosts": 8,
            "offline_hosts": 2
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mcp_client.execute_tool("get_fleet_status", {})
            
            assert result.success is True
            assert result.data == mock_response_data
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_get_fleet_status_error(self, mcp_client):
        """Test fleet status retrieval with error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            
            result = await mcp_client.execute_tool("get_fleet_status", {})
            
            assert result.success is False
            assert "Connection failed" in result.error
    
    @pytest.mark.asyncio
    async def test_get_host_details_success(self, mcp_client):
        """Test successful host details retrieval."""
        hostname = "test-host.example.com"
        mock_response_data = {
            "hostname": hostname,
            "os_name": "Ubuntu 22.04",
            "status": "online"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mcp_client.execute_tool("get_host_details", {"hostname": hostname})
            
            assert result.success is True
            assert result.data == mock_response_data
    
    @pytest.mark.asyncio
    async def test_get_host_details_missing_hostname(self, mcp_client):
        """Test host details retrieval without hostname."""
        result = await mcp_client.execute_tool("get_host_details", {})
        
        assert result.success is False
        assert "hostname is required" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_get_host_details_not_found(self, mcp_client):
        """Test host details retrieval for non-existent host."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            
            error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=error)
            
            result = await mcp_client.execute_tool("get_host_details", {"hostname": "nonexistent"})
            
            assert result.success is False
            assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_schedule_updates_success(self, mcp_client):
        """Test successful update scheduling."""
        params = {
            "hostnames": ["host1.example.com", "host2.example.com"],
            "schedule": "2024-01-01T10:00:00Z",
            "update_type": "security"
        }
        
        mock_response_data = {"job_id": "12345", "status": "scheduled"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mcp_client.execute_tool("schedule_updates", params)
            
            assert result.success is True
            assert result.data == mock_response_data
    
    @pytest.mark.asyncio
    async def test_schedule_updates_missing_params(self, mcp_client):
        """Test update scheduling with missing parameters."""
        # Missing hostnames
        result = await mcp_client.execute_tool("schedule_updates", {"schedule": "2024-01-01T10:00:00Z"})
        assert result.success is False
        assert "hostnames" in result.error.lower()
        
        # Missing schedule
        result = await mcp_client.execute_tool("schedule_updates", {"hostnames": ["host1"]})
        assert result.success is False
        assert "schedule" in result.error.lower()


@pytest.mark.asyncio
async def test_generic_http_error_handling():
    """Test generic HTTP error handling."""
    client = FleetPulseMCPClient()
    
    with patch('httpx.AsyncClient') as mock_client:
        # Simulate network error
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.ConnectError("Network unreachable")
        )
        
        result = await client.execute_tool("get_fleet_status", {})
        
        assert result.success is False
        assert "Network unreachable" in result.error


def test_tool_parameter_schema():
    """Test that tool parameter schemas are properly defined."""
    client = FleetPulseMCPClient()
    
    # Test get_host_details parameters
    tool = client.get_tool("get_host_details")
    assert "hostname" in tool.parameters
    assert tool.parameters["hostname"]["required"] is True
    
    # Test get_update_history parameters
    tool = client.get_tool("get_update_history")
    assert "hostname" in tool.parameters
    assert "days" in tool.parameters
    assert tool.parameters["hostname"]["required"] is True
    assert tool.parameters["days"]["required"] is False