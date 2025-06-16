"""MCP Client for FleetPulse integration."""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of MCP tool errors."""
    TOOL_NOT_FOUND = "tool_not_found"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    SERVER_ERROR = "server_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class MCPToolResult:
    """MCP tool execution result."""
    success: bool
    data: Any
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    execution_time: Optional[float] = None
    diagnostics: Optional[Dict[str, Any]] = None


@dataclass
class MCPDiagnostics:
    """Diagnostic information for MCP operations."""
    backend_status: Optional[str] = None
    database_accessible: Optional[bool] = None
    network_connectivity: Optional[bool] = None
    last_successful_call: Optional[str] = None
    error_count: int = 0
    performance_metrics: Optional[Dict[str, float]] = None


class FleetPulseMCPClient:
    """Client for FleetPulse MCP integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.fleetpulse_api_url
        self.tools = self._register_tools()
        self.diagnostics = MCPDiagnostics()
        self._error_count = 0
        self._last_health_check = None
        self._health_check_interval = 300  # 5 minutes
    
    async def get_diagnostics(self) -> MCPDiagnostics:
        """Get current diagnostic information."""
        await self._update_diagnostics()
        return self.diagnostics
    
    async def _update_diagnostics(self):
        """Update diagnostic information."""
        try:
            # Check backend health
            start_time = time.time()
            backend_healthy = await self._check_backend_health()
            health_check_time = time.time() - start_time
            
            self.diagnostics.backend_status = "healthy" if backend_healthy else "unhealthy"
            self.diagnostics.network_connectivity = backend_healthy
            
            if not hasattr(self.diagnostics, 'performance_metrics') or self.diagnostics.performance_metrics is None:
                self.diagnostics.performance_metrics = {}
            
            self.diagnostics.performance_metrics["health_check_time"] = health_check_time
            self.diagnostics.error_count = self._error_count
            
            # Check database accessibility (through API)
            try:
                await self._test_database_connectivity()
                self.diagnostics.database_accessible = True
            except Exception as e:
                logger.warning(f"Database connectivity test failed: {e}")
                self.diagnostics.database_accessible = False
                
        except Exception as e:
            logger.error(f"Failed to update diagnostics: {e}")
    
    async def _check_backend_health(self) -> bool:
        """Check if FleetPulse backend is healthy."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Backend health check failed: {e}")
            return False
    
    async def _test_database_connectivity(self):
        """Test database connectivity through API."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/api/hosts?limit=1")
            response.raise_for_status()
    
    def _classify_error(self, error: Exception, response: Optional[httpx.Response] = None) -> ErrorType:
        """Classify error type for better handling."""
        if isinstance(error, httpx.TimeoutException):
            return ErrorType.TIMEOUT_ERROR
        elif isinstance(error, httpx.ConnectError):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, httpx.HTTPStatusError):
            if response and response.status_code == 401:
                return ErrorType.AUTHENTICATION_ERROR
            elif response and response.status_code == 404:
                return ErrorType.TOOL_NOT_FOUND
            elif response and response.status_code >= 500:
                return ErrorType.SERVER_ERROR
            elif response and response.status_code == 400:
                return ErrorType.VALIDATION_ERROR
            else:
                return ErrorType.SERVER_ERROR
        elif "database" in str(error).lower() or "sqlite" in str(error).lower():
            return ErrorType.DATABASE_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _get_error_guidance(self, error_type: ErrorType, tool_name: str) -> str:
        """Get user-friendly error guidance based on error type."""
        guidance_map = {
            ErrorType.TOOL_NOT_FOUND: f"The {tool_name} tool or resource was not found. This could indicate an API endpoint change or the resource doesn't exist.",
            ErrorType.NETWORK_ERROR: f"Unable to connect to FleetPulse backend. Please check if the service is running on {self.base_url} and verify network connectivity.",
            ErrorType.DATABASE_ERROR: "Database access issue detected. The FleetPulse database may be locked, corrupted, or inaccessible. Check database file permissions and run integrity checks.",
            ErrorType.AUTHENTICATION_ERROR: "Authentication failed. Please verify API keys, tokens, or service account configuration.",
            ErrorType.VALIDATION_ERROR: f"Invalid parameters provided to {tool_name}. Please check the parameter format and required fields.",
            ErrorType.TIMEOUT_ERROR: f"Request to {tool_name} timed out. The backend service may be overloaded or experiencing performance issues.",
            ErrorType.SERVER_ERROR: f"FleetPulse backend server error occurred while executing {tool_name}. Check backend service logs for details.",
            ErrorType.UNKNOWN_ERROR: f"An unexpected error occurred with {tool_name}. Check logs for detailed error information."
        }
        return guidance_map.get(error_type, "An unknown error occurred.")
    
    async def _create_error_result(self, tool_name: str, error: Exception, response: Optional[httpx.Response] = None) -> MCPToolResult:
        """Create a comprehensive error result with diagnostics."""
        self._error_count += 1
        error_type = self._classify_error(error, response)
        guidance = self._get_error_guidance(error_type, tool_name)
        
        # Gather diagnostic information
        diagnostics = {
            "error_type": error_type.value,
            "error_message": str(error),
            "backend_url": self.base_url,
            "timestamp": time.time(),
            "guidance": guidance
        }
        
        if response:
            diagnostics["status_code"] = response.status_code
            diagnostics["response_headers"] = dict(response.headers)
        
        # Add suggested recovery actions
        recovery_actions = self._get_recovery_actions(error_type)
        diagnostics["recovery_actions"] = recovery_actions
        
        logger.error(f"Tool {tool_name} failed: {error_type.value} - {error}")
        
        return MCPToolResult(
            success=False,
            data=None,
            error=f"{guidance}\n\nTechnical details: {str(error)}",
            error_type=error_type,
            diagnostics=diagnostics
        )
    
    def _get_recovery_actions(self, error_type: ErrorType) -> List[str]:
        """Get specific recovery actions for each error type."""
        actions_map = {
            ErrorType.NETWORK_ERROR: [
                "Check if FleetPulse backend service is running",
                "Verify network connectivity to the backend",
                "Test with: curl -f {}/health".format(self.base_url),
                "Check firewall and proxy settings"
            ],
            ErrorType.DATABASE_ERROR: [
                "Check database file permissions",
                "Run SQLite integrity check: sqlite3 fleetpulse.db 'PRAGMA integrity_check;'",
                "Verify database is not locked by other processes",
                "Consider restarting FleetPulse backend service"
            ],
            ErrorType.TIMEOUT_ERROR: [
                "Check backend service performance and load",
                "Verify system resources (CPU, memory, disk)",
                "Consider increasing timeout values",
                "Check for long-running database queries"
            ],
            ErrorType.AUTHENTICATION_ERROR: [
                "Verify API authentication configuration",
                "Check service account permissions",
                "Refresh authentication tokens if applicable"
            ],
            ErrorType.SERVER_ERROR: [
                "Check FleetPulse backend service logs",
                "Restart backend service if needed",
                "Verify system resources availability",
                "Check for recent configuration changes"
            ]        }
        return actions_map.get(error_type, ["Check logs for more details", "Contact system administrator"])

    def _register_tools(self) -> Dict[str, MCPTool]:
        """Register available MCP tools for FleetPulse."""
        return {
            "health_check": MCPTool(
                name="health_check",
                description="Check backend and MCP server health status",
                parameters={}
            ),
            "list_hosts": MCPTool(
                name="list_hosts",
                description="List all hosts with metadata (OS, last update, package count)",
                parameters={}
            ),
            "get_host_details": MCPTool(
                name="get_host_details",
                description="Get detailed information about a specific host",
                parameters={
                    "hostname": {
                        "type": "string",
                        "description": "Name of the host to query",
                        "required": True
                    }
                }
            ),
            "get_update_reports": MCPTool(
                name="get_update_reports",
                description="Retrieve package update reports with filtering",
                parameters={
                    "hostname": {
                        "type": "string",
                        "description": "Filter by hostname (optional)",
                        "required": False
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30)",
                        "required": False,
                        "default": 30
                    }
                }
            ),
            "get_host_reports": MCPTool(
                name="get_host_reports",
                description="Get update reports for a specific host",
                parameters={
                    "hostname": {
                        "type": "string",
                        "description": "Name of the host",
                        "required": True
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30)",
                        "required": False,
                        "default": 30
                    }
                }
            ),
            "list_packages": MCPTool(
                name="list_packages",
                description="List all packages across the fleet",
                parameters={
                    "search": {
                        "type": "string",
                        "description": "Search term to filter packages (optional)",
                        "required": False
                    }
                }
            ),
            "get_package_details": MCPTool(
                name="get_package_details",
                description="Get detailed package information across the fleet",
                parameters={
                    "package_name": {
                        "type": "string",
                        "description": "Name of the package",
                        "required": True
                    }
                }
            ),
            "get_fleet_statistics": MCPTool(
                name="get_fleet_statistics",
                description="Get aggregate statistics and activity metrics",
                parameters={}
            ),
            "search": MCPTool(
                name="search",
                description="Search across hosts, packages, and reports",
                parameters={
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "required": True
                    }
                }
            )
        }
    def get_available_tools(self) -> List[MCPTool]:
        """Get list of available MCP tools."""
        return list(self.tools.values())
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool definition by name."""
        return self.tools.get(tool_name)
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Execute an MCP tool with given parameters."""
        start_time = time.time()
        
        if tool_name not in self.tools:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}",
                error_type=ErrorType.TOOL_NOT_FOUND,
                execution_time=time.time() - start_time
            )
        
        # Perform periodic health checks
        if (self._last_health_check is None or 
            time.time() - self._last_health_check > self._health_check_interval):
            await self._update_diagnostics()
            self._last_health_check = time.time()
        
        try:
            # Route to appropriate handler using actual FleetPulse API endpoints
            if tool_name == "health_check":
                result = await self._call_api_endpoint("GET", "/health")
            elif tool_name == "list_hosts":
                result = await self._call_api_endpoint("GET", "/api/hosts")
            elif tool_name == "get_host_details":
                hostname = parameters.get("hostname")
                if not hostname:
                    return MCPToolResult(
                        success=False,
                        data=None,
                        error="hostname parameter is required",
                        error_type=ErrorType.VALIDATION_ERROR,
                        execution_time=time.time() - start_time
                    )
                result = await self._call_api_endpoint("GET", f"/api/hosts/{hostname}")
            elif tool_name == "get_update_reports":
                params = {}
                if parameters.get("hostname"):
                    params["hostname"] = parameters["hostname"]
                if parameters.get("days"):
                    params["days"] = parameters["days"]
                result = await self._call_api_endpoint("GET", "/api/reports", params)
            elif tool_name == "get_host_reports":
                hostname = parameters.get("hostname")
                if not hostname:
                    return MCPToolResult(
                        success=False,
                        data=None,
                        error="hostname parameter is required",
                        error_type=ErrorType.VALIDATION_ERROR,
                        execution_time=time.time() - start_time
                    )
                params = {}
                if parameters.get("days"):
                    params["days"] = parameters["days"]
                result = await self._call_api_endpoint("GET", f"/api/hosts/{hostname}/reports", params)
            elif tool_name == "list_packages":
                params = {}
                if parameters.get("search"):
                    params["search"] = parameters["search"]
                result = await self._call_api_endpoint("GET", "/api/packages", params)
            elif tool_name == "get_package_details":
                package_name = parameters.get("package_name")
                if not package_name:
                    return MCPToolResult(
                        success=False,
                        data=None,
                        error="package_name parameter is required",
                        error_type=ErrorType.VALIDATION_ERROR,
                        execution_time=time.time() - start_time
                    )
                result = await self._call_api_endpoint("GET", f"/api/packages/{package_name}")
            elif tool_name == "get_fleet_statistics":
                result = await self._call_api_endpoint("GET", "/api/stats")
            elif tool_name == "search":
                query = parameters.get("query")
                if not query:
                    return MCPToolResult(
                        success=False,
                        data=None,
                        error="query parameter is required",
                        error_type=ErrorType.VALIDATION_ERROR,
                        execution_time=time.time() - start_time
                    )
                params = {"q": query}
                result = await self._call_api_endpoint("GET", "/api/search", params)
            else:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Tool '{tool_name}' not implemented",
                    error_type=ErrorType.TOOL_NOT_FOUND,
                    execution_time=time.time() - start_time
                )
            
            # Add execution time to successful results
            result.execution_time = time.time() - start_time
            
            # Update last successful call timestamp
            if result.success:
                self.diagnostics.last_successful_call = str(time.time())
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return await self._create_error_result(tool_name, e)
    
    async def _call_api_endpoint(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> MCPToolResult:
        """Helper method to call FleetPulse API endpoints."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}{endpoint}"
                
                if method.upper() == "GET":
                    response = await client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, json=params)
                else:
                    return MCPToolResult(
                        success=False,
                        data=None,
                        error=f"Unsupported HTTP method: {method}"
                    )
                
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
                
        except httpx.HTTPStatusError as e:
            error_type = self._classify_error(e, e.response)
            return await self._create_error_result(endpoint, e, e.response)
        except Exception as e:
            return await self._create_error_result(endpoint, e)