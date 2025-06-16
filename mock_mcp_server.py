"""
Simple mock MCP server for testing the FleetPulse chatbot MCP integration.
This creates a minimal HTTP server that responds to MCP requests.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

app = FastAPI(title="Mock MCP Server")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "server": "mock-mcp"}

@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """Mock MCP endpoint that handles tools/list and tools/call requests."""
    
    method = request.get("method", "")
    
    if method == "tools/list":
        # Return mock tools
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "mock_fleet_status",
                        "description": "Get mock fleet status information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "mock_system_info", 
                        "description": "Get mock system information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hostname": {
                                    "type": "string",
                                    "description": "Hostname to query"
                                }
                            },
                            "required": []
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        # Handle tool calls
        params = request.get("params", {})
        tool_name = params.get("name", "")
        
        if tool_name == "mock_fleet_status":
            return {
                "jsonrpc": "2.0", 
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Mock Fleet Status:\n- Total Hosts: 5\n- Online: 4\n- Offline: 1\n- Pending Updates: 12"
                        }
                    ]
                }
            }
        elif tool_name == "mock_system_info":
            hostname = params.get("arguments", {}).get("hostname", "unknown")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"), 
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Mock System Info for {hostname}:\n- OS: Ubuntu 22.04\n- Kernel: 5.15.0\n- Uptime: 15 days\n- Load: 0.5, 0.3, 0.2"
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
    
    else:
        return {
            "jsonrpc": "2.0", 
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

if __name__ == "__main__":
    print("Starting Mock MCP Server on http://localhost:8002")
    print("Available tools: mock_fleet_status, mock_system_info")
    uvicorn.run(app, host="localhost", port=8002)
