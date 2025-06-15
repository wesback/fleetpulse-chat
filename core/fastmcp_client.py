"""Real MCP Client for FastMCP server integration."""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass, asdict
import httpx
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from config import get_settings

logger = logging.getLogger(__name__)


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
            return False
    
    async def _initialize_http(self) -> bool:
        """Initialize HTTP connection to FastMCP server."""
        if not self.server_url:
            logger.error("MCP_SERVER_URL required for HTTP connection")
            return False
        
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        # Test connection and get tools
        try:
            tools = await self._list_tools_http()
            self._tools = {tool.name: tool for tool in tools}
            self._initialized = True
            logger.info(f"Connected to FastMCP server via HTTP. Found {len(self._tools)} tools.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to FastMCP server: {e}")
            return False
    
    async def _initialize_websocket(self) -> bool:
        """Initialize WebSocket connection to FastMCP server."""
        if not self.server_url:
            logger.error("MCP_SERVER_URL required for WebSocket connection")
            return False
        
        try:
            self._websocket = await websockets.connect(
                self.server_url,
                timeout=self.timeout
            )
            
            # Initialize MCP session
            init_request = MCPRequest(
                method="initialize",
                params={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "fleetpulse-chatbot",
                        "version": "1.0.0"
                    }
                }
            )
            
            response = await self._send_websocket_request(init_request)
            if response.error:
                logger.error(f"MCP initialization failed: {response.error}")
                return False
            
            # Get available tools
            tools = await self._list_tools_websocket()
            self._tools = {tool.name: tool for tool in tools}
            self._initialized = True
            logger.info(f"Connected to FastMCP server via WebSocket. Found {len(self._tools)} tools.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to FastMCP server: {e}")
            return False
    
    async def _initialize_stdio(self) -> bool:
        """Initialize stdio connection to FastMCP server."""
        logger.error("STDIO connection not yet implemented")
        return False
    
    async def _list_tools_http(self) -> List[MCPTool]:
        """List available tools via HTTP."""
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
            for tool_data in mcp_response.result.get("tools", []):
                tools.append(MCPTool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    inputSchema=tool_data["inputSchema"]
                ))
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise
    
    async def _list_tools_websocket(self) -> List[MCPTool]:
        """List available tools via WebSocket."""
        try:
            request = MCPRequest(method="tools/list")
            response = await self._send_websocket_request(request)
            
            if response.error:
                raise Exception(f"MCP error: {response.error}")
            
            tools = []
            for tool_data in response.result.get("tools", []):
                tools.append(MCPTool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    inputSchema=tool_data["inputSchema"]
                ))
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
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
            logger.error(f"WebSocket communication error: {e}")
            raise
    
    async def get_available_tools(self) -> List[MCPTool]:
        """Get list of available MCP tools."""
        if not self._initialized:
            await self.initialize()
        
        return list(self._tools.values())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Execute an MCP tool with given parameters."""
        if not self._initialized:
            await self.initialize()
        
        if tool_name not in self._tools:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        try:
            if self.connection_type == "http":
                return await self._execute_tool_http(tool_name, parameters)
            elif self.connection_type == "websocket":
                return await self._execute_tool_websocket(tool_name, parameters)
            else:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Connection type {self.connection_type} not supported"
                )
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _execute_tool_http(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Execute tool via HTTP."""
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
    
    async def _execute_tool_websocket(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Execute tool via WebSocket."""
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
        """Close the MCP connection."""
        try:
            if self._websocket:
                await self._websocket.close()
                self._websocket = None
            
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None
            
            self._initialized = False
            logger.info("MCP client connection closed")
            
        except Exception as e:
            logger.error(f"Error closing MCP client: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Factory function to get the appropriate MCP client
async def get_mcp_client() -> FastMCPClient:
    """Get configured MCP client instance."""
    settings = get_settings()
    
    if not settings.mcp_server_url and not settings.mcp_server_command:
        logger.warning("No MCP server configured, using legacy REST API client")
        # Fall back to legacy implementation
        from .mcp_client import FleetPulseMCPClient
        return FleetPulseMCPClient()
    
    return FastMCPClient()
