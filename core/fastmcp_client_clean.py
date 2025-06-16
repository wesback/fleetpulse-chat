"""Clean MCP Client for FastMCP server integration."""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

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
class MCPRequest:
    """MCP request message."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class MCPResponse:
    """MCP response message."""
    jsonrpc: str
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


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


class FastMCPClient:
    """Client for connecting to FastMCP servers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.connection_type = self.settings.mcp_connection_type
        self.server_url = self.settings.mcp_server_url
        self.server_command = self.settings.mcp_server_command
        self.timeout = self.settings.mcp_timeout
        self.max_retries = self.settings.mcp_max_retries
        
        self._tools: Dict[str, MCPTool] = {}
        self._websocket = None
        self._http_client = None
        self._initialized = False
        
        # Diagnostics tracking
        self.diagnostics = MCPDiagnostics()
        self._error_count = 0
        self._last_health_check = None
        self._health_check_interval = 300  # 5 minutes
    
    async def initialize(self) -> bool:
        """Initialize connection to MCP server."""
        try:
            if self.connection_type == "http":
                return await self._initialize_http()
            elif self.connection_type == "websocket":
                return await self._initialize_websocket()
            elif self.connection_type == "stdio":
                return await self._initialize_stdio()
            else:
                logger.error(f"Unsupported connection type: {self.connection_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            self._error_count += 1
            return False
    
    async def _initialize_http(self) -> bool:
        """Initialize HTTP connection to FastMCP server."""
        if not self.server_url:
            logger.error("MCP_SERVER_URL required for HTTP connection")
            self.diagnostics.backend_status = "No server URL configured"
            return False
        
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        # Test connection and get tools
        try:
            # First test if the server is reachable
            try:
                health_response = await self._http_client.get(f"{self.server_url}/health")
                logger.info(f"MCP server health check: {health_response.status_code}")
            except:
                # Health endpoint might not exist, continue with tools list
                pass
            
            tools = await self._list_tools_http()
            self._tools = {tool.name: tool for tool in tools}
            self._initialized = True
            self.diagnostics.backend_status = "Connected"
            self.diagnostics.network_connectivity = True
            self.diagnostics.last_successful_call = str(time.time())
            logger.info(f"FastMCP HTTP client initialized with {len(self._tools)} tools")
            return True
            
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to MCP server at {self.server_url}: {e}")
            self.diagnostics.backend_status = f"Connection failed: {e}"
            self.diagnostics.network_connectivity = False
            self._error_count += 1
            return False
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to MCP server: {e}")
            self.diagnostics.backend_status = f"Timeout: {e}"
            self.diagnostics.network_connectivity = False
            self._error_count += 1
            return False
        except Exception as e:
            logger.error(f"Failed to initialize HTTP client: {e}")
            self.diagnostics.backend_status = f"Init failed: {e}"
            self._error_count += 1
            return False
    
    async def _initialize_websocket(self) -> bool:
        """Initialize WebSocket connection to FastMCP server."""
        if not self.server_url:
            logger.error("MCP_SERVER_URL required for WebSocket connection")
            return False
        
        try:
            ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://")
            if not ws_url.startswith(("ws://", "wss://")):
                ws_url = f"ws://{ws_url}"
            
            self._websocket = await websockets.connect(ws_url)
            
            # Test connection and get tools
            tools = await self._list_tools_websocket()
            self._tools = {tool.name: tool for tool in tools}
            self._initialized = True
            logger.info(f"FastMCP WebSocket client initialized with {len(self._tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to FastMCP server: {e}")
            self._error_count += 1
            return False
    
    async def _initialize_stdio(self) -> bool:
        """Initialize stdio connection to FastMCP server."""
        logger.error("STDIO connection not yet implemented")
        return False
    
    async def _list_tools_http(self) -> List[MCPTool]:
        """List available tools via HTTP."""
        if not self._http_client:
            raise Exception("HTTP client not initialized")
            
        try:
            response = await self._http_client.post(
                f"{self.server_url}/mcp",
                json=asdict(MCPRequest(method="tools/list"))
            )
            response.raise_for_status()
            
            mcp_response = MCPResponse(**response.json())
            if mcp_response.error:
                raise Exception(f"MCP error: {mcp_response.error}")
            
            tools = []
            if mcp_response.result:
                for tool_data in mcp_response.result.get("tools", []):
                    tools.append(MCPTool(
                        name=tool_data["name"],
                        description=tool_data["description"],
                        inputSchema=tool_data["inputSchema"]
                    ))
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            self._error_count += 1
            raise
    
    async def _list_tools_websocket(self) -> List[MCPTool]:
        """List available tools via WebSocket."""
        try:
            request = MCPRequest(method="tools/list")
            response = await self._send_websocket_request(request)
            
            if response.error:
                raise Exception(f"MCP error: {response.error}")
            
            tools = []
            if response.result:
                for tool_data in response.result.get("tools", []):
                    tools.append(MCPTool(
                        name=tool_data["name"],
                        description=tool_data["description"],
                        inputSchema=tool_data["inputSchema"]
                    ))
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            self._error_count += 1
            raise
    
    async def _send_websocket_request(self, request: MCPRequest) -> MCPResponse:
        """Send request via WebSocket and wait for response."""
        if not self._websocket:
            raise Exception("WebSocket not connected")
        
        try:
            await self._websocket.send(json.dumps(asdict(request)))
            response_data = await self._websocket.recv()
            return MCPResponse(**json.loads(response_data))
        except (ConnectionClosed, WebSocketException) as e:
            logger.error(f"WebSocket error: {e}")
            self._error_count += 1
            raise Exception(f"WebSocket communication failed: {e}")
    
    async def list_tools(self) -> List[MCPTool]:
        """Get list of available tools."""
        if not self._initialized:
            raise Exception("MCP client not initialized")
        
        return list(self._tools.values())
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Call a tool with given parameters."""
        if not self._initialized:
            return MCPToolResult(
                success=False,
                data=None,
                error="MCP client not initialized",
                error_type=ErrorType.SERVER_ERROR
            )
        
        if tool_name not in self._tools:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found",
                error_type=ErrorType.TOOL_NOT_FOUND
            )
        
        start_time = time.time()
        
        try:
            if self.connection_type == "http":
                result = await self._call_tool_http(tool_name, parameters)
            elif self.connection_type == "websocket":
                result = await self._call_tool_websocket(tool_name, parameters)
            else:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Unsupported connection type: {self.connection_type}",
                    error_type=ErrorType.SERVER_ERROR
                )
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            if result.success:
                self.diagnostics.last_successful_call = str(time.time())
            else:
                self._error_count += 1
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._error_count += 1
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e),
                error_type=ErrorType.UNKNOWN_ERROR,
                execution_time=execution_time
            )
    
    async def _call_tool_http(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Call tool via HTTP."""
        if not self._http_client:
            raise Exception("HTTP client not initialized")
            
        try:
            request = MCPRequest(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": parameters
                }
            )
            
            response = await self._http_client.post(
                f"{self.server_url}/mcp",
                json=asdict(request)
            )
            response.raise_for_status()
            
            mcp_response = MCPResponse(**response.json())
            if mcp_response.error:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"MCP error: {mcp_response.error}"
                )
            
            return MCPToolResult(
                success=True,
                data=mcp_response.result
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _call_tool_websocket(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Call tool via WebSocket."""
        try:
            request = MCPRequest(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": parameters
                }
            )
            
            response = await self._send_websocket_request(request)
            
            if response.error:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"MCP error: {response.error}"
                )
            
            return MCPToolResult(
                success=True,
                data=response.result
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def close(self):
        """Clean up resources."""
        try:
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None
            
            if self._websocket:
                await self._websocket.close()
                self._websocket = None
                
            self._initialized = False
            
        except Exception as e:
            logger.error(f"Error closing MCP client: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Execute a tool with given parameters. Alias for call_tool for compatibility."""
        return await self.call_tool(tool_name, parameters)


# Factory function to get the appropriate MCP client
async def get_mcp_client() -> FastMCPClient:
    """Get configured MCP client instance."""
    settings = get_settings()
    
    # Always use FastMCPClient; do not fall back to legacy REST client
    client = FastMCPClient()
    
    # Initialize the client connection
    try:
        success = await client.initialize()
        if success:
            logger.info("MCP client initialized successfully")
        else:
            logger.warning("MCP client failed to initialize - tools will be offline")
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        # Return the client anyway - tools will show as offline but app won't crash
    
    return client
