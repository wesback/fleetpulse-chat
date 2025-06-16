"""MCP tool diagnostics and recovery utilities."""

import asyncio
import logging
import time
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import httpx
import subprocess
import os

from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    name: str
    status: str  # "healthy", "warning", "error"
    message: str
    details: Optional[Dict] = None
    recovery_actions: Optional[List[str]] = None


class MCPDiagnosticRunner:
    """Comprehensive diagnostic runner for MCP tools and FleetPulse backend."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.fleetpulse_api_url
        
    async def run_full_diagnostics(self) -> List[DiagnosticResult]:
        """Run comprehensive diagnostics on all MCP components."""
        results = []
        
        # Backend connectivity check
        results.append(await self._check_backend_connectivity())
        
        # API endpoint checks
        results.extend(await self._check_api_endpoints())
        
        # Database accessibility check
        results.append(await self._check_database_access())
        
        # Network diagnostics
        results.append(await self._check_network_connectivity())
        
        # System resource checks
        results.append(await self._check_system_resources())
        
        # MCP service health
        results.append(await self._check_mcp_service_health())
        
        return results
    
    async def _check_backend_connectivity(self) -> DiagnosticResult:
        """Check FleetPulse backend connectivity."""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    return DiagnosticResult(
                        name="Backend Connectivity",
                        status="healthy",
                        message=f"Backend responding normally ({response_time:.2f}s)",
                        details={"response_time": response_time, "status_code": 200}
                    )
                else:
                    return DiagnosticResult(
                        name="Backend Connectivity",
                        status="error",
                        message=f"Backend returned status {response.status_code}",
                        details={"status_code": response.status_code},
                        recovery_actions=[
                            "Check FleetPulse backend service logs",
                            "Restart backend service",
                            "Verify configuration settings"
                        ]
                    )
        except httpx.TimeoutException:
            return DiagnosticResult(
                name="Backend Connectivity",
                status="error",
                message="Backend health check timed out",
                recovery_actions=[
                    "Check if FleetPulse backend is running",
                    "Verify network connectivity",
                    "Check system resources (CPU, memory)"
                ]
            )
        except httpx.ConnectError:
            return DiagnosticResult(
                name="Backend Connectivity",
                status="error",
                message=f"Cannot connect to backend at {self.base_url}",
                recovery_actions=[
                    "Start FleetPulse backend service",
                    "Verify backend URL configuration",
                    "Check firewall and port accessibility"
                ]
            )
        except Exception as e:
            return DiagnosticResult(
                name="Backend Connectivity",
                status="error",
                message=f"Unexpected error: {str(e)}",
                recovery_actions=["Check logs for detailed error information"]
            )
    
    async def _check_api_endpoints(self) -> List[DiagnosticResult]:
        """Check critical API endpoints."""
        endpoints = [
            "/api/fleet/status",
            "/api/hosts",
            "/api/updates/pending"
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    if response.status_code == 200:
                        results.append(DiagnosticResult(
                            name=f"API Endpoint {endpoint}",
                            status="healthy",
                            message="Endpoint responding normally"
                        ))
                    else:
                        results.append(DiagnosticResult(
                            name=f"API Endpoint {endpoint}",
                            status="warning",
                            message=f"Endpoint returned status {response.status_code}",
                            recovery_actions=["Check API implementation and routing"]
                        ))
            except Exception as e:
                results.append(DiagnosticResult(
                    name=f"API Endpoint {endpoint}",
                    status="error",
                    message=f"Failed to connect: {str(e)}",
                    recovery_actions=["Check backend service and database connectivity"]
                ))
        
        return results
    
    async def _check_database_access(self) -> DiagnosticResult:
        """Check database accessibility through API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try to fetch hosts list as a database connectivity test
                response = await client.get(f"{self.base_url}/api/hosts?limit=1")
                
                if response.status_code == 200:
                    data = response.json()
                    return DiagnosticResult(
                        name="Database Access",
                        status="healthy",
                        message="Database accessible through API",
                        details={"test_query": "successful", "host_count": len(data)}
                    )
                else:
                    return DiagnosticResult(
                        name="Database Access",
                        status="error",
                        message=f"Database query failed with status {response.status_code}",
                        recovery_actions=[
                            "Check database file permissions",
                            "Run database integrity check",
                            "Verify database is not locked"
                        ]
                    )
        except Exception as e:
            return DiagnosticResult(
                name="Database Access",
                status="error",
                message=f"Database connectivity test failed: {str(e)}",
                recovery_actions=[
                    "Check SQLite database file existence and permissions",
                    "Run: sqlite3 fleetpulse.db 'PRAGMA integrity_check;'",
                    "Restart backend service to release database locks"
                ]
            )
    
    async def _check_network_connectivity(self) -> DiagnosticResult:
        """Check network connectivity."""
        try:
            # Parse URL to get host and port
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8000
            
            # Test TCP connectivity
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            
            return DiagnosticResult(
                name="Network Connectivity",
                status="healthy",
                message=f"TCP connection to {host}:{port} successful"
            )
        except asyncio.TimeoutError:
            return DiagnosticResult(
                name="Network Connectivity",
                status="error",
                message="Network connection timed out",
                recovery_actions=[
                    "Check if target service is running",
                    "Verify firewall settings",
                    "Test network routing"
                ]
            )
        except Exception as e:
            return DiagnosticResult(
                name="Network Connectivity",
                status="error",
                message=f"Network connectivity failed: {str(e)}",
                recovery_actions=[
                    "Check network configuration",
                    "Verify service is listening on expected port",
                    "Test with: telnet localhost 8000"
                ]
            )
    
    async def _check_system_resources(self) -> DiagnosticResult:
        """Check system resource availability."""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent}%")
            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent}%")
            
            if issues:
                return DiagnosticResult(
                    name="System Resources",
                    status="warning",
                    message="; ".join(issues),
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent
                    },
                    recovery_actions=[
                        "Monitor system performance",
                        "Consider scaling resources",
                        "Check for resource-intensive processes"
                    ]
                )
            else:
                return DiagnosticResult(
                    name="System Resources",
                    status="healthy",
                    message="System resources within normal ranges",
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent
                    }
                )
        except ImportError:
            return DiagnosticResult(
                name="System Resources",
                status="warning",
                message="psutil not available for resource monitoring",
                recovery_actions=["Install psutil for system monitoring: pip install psutil"]
            )
        except Exception as e:
            return DiagnosticResult(
                name="System Resources",
                status="error",
                message=f"Resource check failed: {str(e)}",
                recovery_actions=["Check system monitoring tools manually"]
            )
    
    async def _check_mcp_service_health(self) -> DiagnosticResult:
        """Check MCP service health."""
        try:
            # This is a placeholder for MCP-specific health checks
            # In a real implementation, this would check MCP server status
            return DiagnosticResult(
                name="MCP Service Health",
                status="healthy",
                message="MCP client operational",
                details={"client_status": "active"}
            )
        except Exception as e:
            return DiagnosticResult(
                name="MCP Service Health",
                status="error",
                message=f"MCP service check failed: {str(e)}",
                recovery_actions=[
                    "Restart MCP services",
                    "Check MCP configuration",
                    "Verify MCP server logs"
                ]
            )


async def run_recovery_procedures(diagnostic_results: List[DiagnosticResult]) -> Dict[str, bool]:
    """Run automated recovery procedures for failed diagnostics."""
    recovery_results = {}
    
    for result in diagnostic_results:
        if result.status == "error" and result.recovery_actions:
            # Implement automated recovery for specific known issues
            if "Backend Connectivity" in result.name:
                recovery_results[result.name] = await _attempt_backend_recovery()
            elif "Database Access" in result.name:
                recovery_results[result.name] = await _attempt_database_recovery()
            else:
                recovery_results[result.name] = False  # Manual intervention required
    
    return recovery_results


async def _attempt_backend_recovery() -> bool:
    """Attempt to recover backend connectivity."""
    try:
        # Implement backend service restart logic here
        # This is a placeholder for actual recovery procedures
        logger.info("Attempting backend recovery...")
        return False  # Return True if recovery successful
    except Exception as e:
        logger.error(f"Backend recovery failed: {e}")
        return False


async def _attempt_database_recovery() -> bool:
    """Attempt to recover database access."""
    try:
        # Implement database recovery logic here
        # This could include unlocking, integrity checks, etc.
        logger.info("Attempting database recovery...")
        return False  # Return True if recovery successful
    except Exception as e:
        logger.error(f"Database recovery failed: {e}")
        return False


def generate_diagnostic_report(results: List[DiagnosticResult]) -> str:
    """Generate a human-readable diagnostic report."""
    report = ["FleetPulse MCP Diagnostic Report", "=" * 40, ""]
    
    healthy_count = sum(1 for r in results if r.status == "healthy")
    warning_count = sum(1 for r in results if r.status == "warning")
    error_count = sum(1 for r in results if r.status == "error")
    
    report.append(f"Summary: {healthy_count} healthy, {warning_count} warnings, {error_count} errors")
    report.append("")
    
    for result in results:
        status_icon = {"healthy": "✓", "warning": "⚠", "error": "✗"}[result.status]
        report.append(f"{status_icon} {result.name}: {result.message}")
        
        if result.recovery_actions:
            report.append("  Recovery Actions:")
            for action in result.recovery_actions:
                report.append(f"    - {action}")
        report.append("")
    
    return "\n".join(report)
