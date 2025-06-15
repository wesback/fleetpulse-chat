"""MCP Client for FleetPulse integration."""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import httpx

from config import get_settings

logger = logging.getLogger(__name__)


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


class FleetPulseMCPClient:
    """Client for FleetPulse MCP integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.fleetpulse_api_url
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, MCPTool]:
        """Register available MCP tools for FleetPulse."""
        return {
            "get_fleet_status": MCPTool(
                name="get_fleet_status",
                description="Get overall fleet health and status summary",
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
            "get_update_history": MCPTool(
                name="get_update_history",
                description="Get package update history for a host",
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
            "get_pending_updates": MCPTool(
                name="get_pending_updates",
                description="Get list of systems with pending updates",
                parameters={
                    "severity": {
                        "type": "string",
                        "description": "Filter by update severity (critical, important, moderate, low)",
                        "required": False
                    }
                }
            ),
            "schedule_updates": MCPTool(
                name="schedule_updates",
                description="Schedule update operations for specified hosts",
                parameters={
                    "hostnames": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of hostnames to update",
                        "required": True
                    },
                    "schedule": {
                        "type": "string",
                        "description": "Schedule time (ISO 8601 format)",
                        "required": True
                    },
                    "update_type": {
                        "type": "string",
                        "description": "Type of update (security, all, specific)",
                        "required": False,
                        "default": "security"
                    }
                }
            ),
            "generate_fleet_report": MCPTool(
                name="generate_fleet_report",
                description="Generate comprehensive fleet report",
                parameters={
                    "format": {
                        "type": "string",
                        "description": "Report format (json, html, pdf)",
                        "required": False,
                        "default": "json"
                    },
                    "include_history": {
                        "type": "boolean",
                        "description": "Include update history in report",
                        "required": False,
                        "default": True
                    }
                }
            ),
            "get_system_metrics": MCPTool(
                name="get_system_metrics",
                description="Get system performance metrics for a host",
                parameters={
                    "hostname": {
                        "type": "string",
                        "description": "Name of the host",
                        "required": True
                    },
                    "metric_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of metrics (cpu, memory, disk, network)",
                        "required": False
                    }
                }
            ),
            "check_package_info": MCPTool(
                name="check_package_info",
                description="Get detailed information about a specific package",
                parameters={
                    "package_name": {
                        "type": "string",
                        "description": "Name of the package",
                        "required": True
                    },
                    "hostname": {
                        "type": "string",
                        "description": "Host to check package on (optional)",
                        "required": False
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
        if tool_name not in self.tools:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        try:
            # Route to appropriate handler
            if tool_name == "get_fleet_status":
                return await self._get_fleet_status()
            elif tool_name == "get_host_details":
                return await self._get_host_details(parameters.get("hostname"))
            elif tool_name == "get_update_history":
                return await self._get_update_history(
                    parameters.get("hostname"),
                    parameters.get("days", 30)
                )
            elif tool_name == "get_pending_updates":
                return await self._get_pending_updates(parameters.get("severity"))
            elif tool_name == "schedule_updates":
                return await self._schedule_updates(
                    parameters.get("hostnames"),
                    parameters.get("schedule"),
                    parameters.get("update_type", "security")
                )
            elif tool_name == "generate_fleet_report":
                return await self._generate_fleet_report(
                    parameters.get("format", "json"),
                    parameters.get("include_history", True)
                )
            elif tool_name == "get_system_metrics":
                return await self._get_system_metrics(
                    parameters.get("hostname"),
                    parameters.get("metric_types")
                )
            elif tool_name == "check_package_info":
                return await self._check_package_info(
                    parameters.get("package_name"),
                    parameters.get("hostname")
                )
            else:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Tool '{tool_name}' not implemented"
                )
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _get_fleet_status(self) -> MCPToolResult:
        """Get overall fleet status."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/fleet/status")
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to get fleet status: {e}"
            )
    
    async def _get_host_details(self, hostname: str) -> MCPToolResult:
        """Get detailed host information."""
        if not hostname:
            return MCPToolResult(
                success=False,
                data=None,
                error="Hostname is required"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/hosts/{hostname}")
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Host '{hostname}' not found"
                )
            raise
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to get host details: {e}"
            )
    
    async def _get_update_history(self, hostname: str, days: int = 30) -> MCPToolResult:
        """Get package update history."""
        if not hostname:
            return MCPToolResult(
                success=False,
                data=None,
                error="Hostname is required"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/hosts/{hostname}/history",
                    params={"days": days}
                )
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to get update history: {e}"
            )
    
    async def _get_pending_updates(self, severity: Optional[str] = None) -> MCPToolResult:
        """Get pending updates across the fleet."""
        try:
            params = {}
            if severity:
                params["severity"] = severity
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/updates/pending",
                    params=params
                )
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to get pending updates: {e}"
            )
    
    async def _schedule_updates(
        self, 
        hostnames: List[str], 
        schedule: str, 
        update_type: str = "security"
    ) -> MCPToolResult:
        """Schedule update operations."""
        if not hostnames:
            return MCPToolResult(
                success=False,
                data=None,
                error="Hostnames list is required"
            )
        
        if not schedule:
            return MCPToolResult(
                success=False,
                data=None,
                error="Schedule is required"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/updates/schedule",
                    json={
                        "hostnames": hostnames,
                        "schedule": schedule,
                        "update_type": update_type
                    }
                )
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to schedule updates: {e}"
            )
    
    async def _generate_fleet_report(
        self, 
        format: str = "json", 
        include_history: bool = True
    ) -> MCPToolResult:
        """Generate fleet report."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/reports/generate",
                    json={
                        "format": format,
                        "include_history": include_history
                    }
                )
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to generate report: {e}"
            )
    
    async def _get_system_metrics(
        self, 
        hostname: str, 
        metric_types: Optional[List[str]] = None
    ) -> MCPToolResult:
        """Get system performance metrics."""
        if not hostname:
            return MCPToolResult(
                success=False,
                data=None,
                error="Hostname is required"
            )
        
        try:
            params = {}
            if metric_types:
                params["metrics"] = ",".join(metric_types)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/hosts/{hostname}/metrics",
                    params=params
                )
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to get system metrics: {e}"
            )
    
    async def _check_package_info(
        self, 
        package_name: str, 
        hostname: Optional[str] = None
    ) -> MCPToolResult:
        """Get package information."""
        if not package_name:
            return MCPToolResult(
                success=False,
                data=None,
                error="Package name is required"
            )
        
        try:
            endpoint = f"{self.base_url}/api/packages/{package_name}"
            params = {}
            if hostname:
                params["hostname"] = hostname
            
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                
                return MCPToolResult(
                    success=True,
                    data=response.json()
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Failed to get package info: {e}"
            )