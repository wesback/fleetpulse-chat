# FastMCP Integration Guide

## Overview

This document explains how to connect the FleetPulse ChatBot to a FastMCP server running in Docker on a different host.

## What is FastMCP?

FastMCP is a Python framework for building Model Context Protocol (MCP) servers. It allows you to expose tools and resources that AI models can use through a standardized protocol.

## Current Implementation

The codebase includes two MCP client implementations:

1. **Legacy (`core/mcp_client.py`)**: REST API client (not real MCP)
2. **FastMCP (`core/fastmcp_client.py`)**: Real MCP protocol client

## Configuration for Remote FastMCP Server

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# MCP Connection Type
MCP_CONNECTION_TYPE=http  # or websocket

# For FastMCP server on different host
MCP_SERVER_URL=http://YOUR_HOST_IP:3001

# Alternative: WebSocket connection
# MCP_SERVER_URL=ws://YOUR_HOST_IP:3001/mcp

# Connection settings
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
```

### 2. Docker Compose Configuration

If running both the ChatBot and FastMCP server via Docker Compose:

```yaml
services:
  fleetpulse-chat:
    # ... existing config ...
    environment:
      - MCP_CONNECTION_TYPE=http
      - MCP_SERVER_URL=http://fleetpulse-mcp:3001
    depends_on:
      - fleetpulse-mcp

  fleetpulse-mcp:
    image: fleetpulse/mcp-server:latest
    ports:
      - "3001:3001"
    environment:
      - FLEETPULSE_API_URL=http://fleetpulse-backend:8000
      - MCP_SERVER_PORT=3001
```

### 3. Remote Host Configuration

For FastMCP server on a different host:

```bash
# In your .env file
MCP_CONNECTION_TYPE=http
MCP_SERVER_URL=http://192.168.1.100:3001  # Replace with actual IP

# Or for WebSocket
MCP_CONNECTION_TYPE=websocket  
MCP_SERVER_URL=ws://192.168.1.100:3001/mcp
```

## FastMCP Server Requirements

Your FastMCP server should:

1. **Expose HTTP/WebSocket endpoint** on port 3001 (or configured port)
2. **Implement MCP protocol** version 2024-11-05
3. **Provide FleetPulse tools** like:
   - `get_fleet_status`
   - `get_host_details`
   - `get_update_history`
   - `schedule_updates`
   - etc.

## Connection Types

### HTTP Connection
- Simpler to set up
- Good for request/response patterns
- Works well with Docker networking
- Default choice for most deployments

### WebSocket Connection  
- Real-time communication
- Better for streaming responses
- Persistent connection
- Good for interactive scenarios

### STDIO Connection
- For local processes only
- Not suitable for Docker containers on different hosts
- Currently not implemented

## Testing the Connection

Use the provided client to test connectivity:

```python
from core.fastmcp_client import FastMCPClient

async def test_connection():
    async with FastMCPClient() as client:
        tools = await client.get_available_tools()
        print(f"Found {len(tools)} tools")
        
        # Test a tool
        result = await client.execute_tool("get_fleet_status", {})
        print(f"Fleet status: {result}")
```

## Troubleshooting

### Connection Issues

1. **Check network connectivity**:
   ```bash
   curl http://YOUR_HOST_IP:3001/health
   ```

2. **Verify FastMCP server is running**:
   ```bash
   docker ps | grep mcp
   ```

3. **Check logs**:
   ```bash
   docker logs fleetpulse-mcp
   ```

### Common Problems

- **Port not accessible**: Ensure port 3001 is open on the remote host
- **Wrong URL format**: Check HTTP vs WebSocket URL format
- **MCP protocol mismatch**: Ensure server implements MCP 2024-11-05
- **Tool not found**: Verify the FastMCP server exposes expected tools

### Network Configuration

For Docker containers on different hosts:

1. **Ensure port forwarding**: `-p 3001:3001`
2. **Check firewall rules**: Allow incoming connections on port 3001
3. **Use correct IP**: Container IP vs host IP
4. **Network mode**: Use `host` networking if needed

## Migration from Legacy Client

The application automatically falls back to the legacy REST API client if no MCP server is configured. To migrate:

1. Set up FastMCP server with proper tools
2. Configure MCP connection settings
3. Test connectivity
4. The application will automatically use FastMCP client

## Security Considerations

- **Network security**: Use HTTPS/WSS in production
- **Authentication**: Implement proper auth in FastMCP server
- **Firewall rules**: Restrict access to MCP port
- **Container security**: Use non-root users in containers

## Performance Optimization

- **Connection pooling**: Reuse HTTP connections
- **Timeout tuning**: Adjust `MCP_TIMEOUT` based on network latency
- **Retry logic**: Configure `MCP_MAX_RETRIES` for reliability
- **Caching**: Cache tool results when appropriate
