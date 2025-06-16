# MCP Tool Error Handling and Diagnostics Guide

This document provides comprehensive guidance for troubleshooting MCP (Model Context Protocol) tool failures in the FleetPulse chatbot application.

## Overview

The FleetPulse chatbot has been enhanced with sophisticated error handling and diagnostic capabilities to help identify and resolve issues with MCP tool execution, particularly the `get_update_history` tool.

## Key Features

### 1. Enhanced Error Classification

The system now automatically classifies errors into specific types:

- **Network Errors**: Connection failures, timeouts
- **Database Errors**: SQLite access issues, corruption, locks
- **Authentication Errors**: API key or permission issues
- **Validation Errors**: Invalid parameters or data format
- **Tool Not Found**: Missing or misconfigured tools
- **Server Errors**: Backend service failures

### 2. Comprehensive Error Display

When an MCP tool fails, the system provides:

- **Clear error messages** with user-friendly explanations
- **Specific error types** for targeted troubleshooting
- **Recovery actions** with step-by-step guidance
- **Technical details** for advanced debugging
- **Diagnostic information** including timestamps and response codes

### 3. Real-time Diagnostics

The chatbot includes built-in diagnostic capabilities:

- **Backend connectivity checks** with response time monitoring
- **Database accessibility tests** through API endpoints
- **Network connectivity validation** with TCP connection tests
- **System resource monitoring** (CPU, memory, disk usage)
- **API endpoint health checks** for critical services

### 4. Automated Recovery

The system includes automated recovery mechanisms:

- **MCP client reset** functionality
- **Connection pool management** 
- **Error count tracking** and reporting
- **Health check scheduling** with configurable intervals
- **Graceful degradation** when services are unavailable

## Common Error Scenarios

### get_update_history Tool Failure

**Symptoms:**
- Tool returns error instead of package update data
- Error messages about connectivity or database access
- Timeouts when querying update history

**Diagnostic Steps:**

1. **Check Backend Connectivity**
   ```bash
   curl -f http://localhost:8000/health
   ```

2. **Verify Database Access**
   ```bash
   sqlite3 fleetpulse.db "PRAGMA integrity_check;"
   ```

3. **Test API Endpoint**
   ```bash
   curl -f http://localhost:8000/api/hosts/homeserver/history?days=7
   ```

4. **Check Service Status**
   ```bash
   systemctl status fleetpulse
   ```

**Recovery Actions:**

1. **Service Restart**
   ```bash
   systemctl restart fleetpulse
   ```

2. **Database Unlock**
   ```bash
   fuser -k fleetpulse.db
   systemctl restart fleetpulse
   ```

3. **Network Troubleshooting**
   ```bash
   netstat -tulpn | grep :8000
   telnet localhost 8000
   ```

## Using the Diagnostic Interface

### Sidebar Diagnostics

The chatbot sidebar includes:

- **Real-time tool status** indicator
- **Quick health check** button
- **Error recovery** panel
- **Latest diagnostic results** summary

### Full Diagnostic Panel

Access via the "🏥 System Diagnostics" button for:

- **Comprehensive system checks** across all components
- **Detailed error analysis** with recovery recommendations
- **Performance metrics** and resource utilization
- **Downloadable diagnostic reports** for documentation

### Quick Recovery Actions

The sidebar provides one-click recovery options:

- **Reset MCP Client**: Reinitialize all MCP connections
- **Health Check**: Quick verification of system status
- **Tool Reset**: Clear error states and retry failed operations

## Error Handling in Code

### Enhanced MCPToolResult

The `MCPToolResult` class now includes:

```python
@dataclass
class MCPToolResult:
    success: bool
    data: Any
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    execution_time: Optional[float] = None
    diagnostics: Optional[Dict[str, Any]] = None
```

### Error Classification

```python
class ErrorType(Enum):
    TOOL_NOT_FOUND = "tool_not_found"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    SERVER_ERROR = "server_error"
    UNKNOWN_ERROR = "unknown_error"
```

### Diagnostic Information

Each error includes detailed diagnostic information:

```python
diagnostics = {
    "error_type": error_type.value,
    "error_message": str(error),
    "backend_url": self.base_url,
    "timestamp": time.time(),
    "guidance": user_friendly_guidance,
    "recovery_actions": specific_recovery_steps,
    "status_code": http_status_code,  # if applicable
    "response_headers": response_headers  # if applicable
}
```

## Troubleshooting Workflow

### 1. Immediate Response
- User reports tool failure
- System displays enhanced error information
- Immediate guidance provided based on error type

### 2. Diagnostic Phase
- Run comprehensive diagnostics via UI
- Identify specific failure points
- Collect performance and connectivity data

### 3. Recovery Phase
- Apply recommended recovery actions
- Monitor system response
- Verify tool functionality restoration

### 4. Prevention
- Monitor error patterns
- Implement proactive health checks
- Update configurations based on findings

## Monitoring and Alerting

### Error Tracking

The system tracks:
- **Error frequency** by tool and type
- **Performance metrics** including response times
- **Recovery success rates**
- **System resource trends**

### Health Monitoring

Regular health checks verify:
- **Backend service availability**
- **Database connectivity and performance**
- **Network path integrity**
- **Authentication token validity**

## Configuration

### Environment Variables

```bash
# FleetPulse Backend
FLEETPULSE_API_URL=http://localhost:8000

# Diagnostic Settings
ENABLE_DEBUG=true
LOG_LEVEL=INFO
HEALTH_CHECK_INTERVAL=300  # seconds

# Error Handling
MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2
TIMEOUT_SECONDS=30
```

### System Prompts

The application includes specialized prompts for:
- **MCP Troubleshooting Specialist**: Focused on tool failure diagnosis
- **Error Handling Specialist**: Recovery procedures and user guidance
- **Diagnostics Specialist**: System health checks and monitoring

## Best Practices

### For Users
1. **Check diagnostic panel** before reporting issues
2. **Use quick health checks** to verify system status
3. **Apply suggested recovery actions** in order
4. **Document persistent issues** for system administrators

### For Administrators
1. **Monitor error patterns** for systemic issues
2. **Schedule regular health checks** during maintenance windows
3. **Maintain database backups** for recovery scenarios
4. **Review diagnostic reports** for performance optimization

### For Developers
1. **Use error classification** for consistent handling
2. **Include recovery guidance** in all error responses
3. **Implement circuit breakers** for failing services
4. **Add comprehensive logging** for debugging

## Support and Resources

### Log Locations
- **Application logs**: `/var/log/fleetpulse-chatbot.log`
- **MCP client logs**: `/var/log/mcp-client.log`
- **Backend service logs**: `/var/log/fleetpulse.log`

### Diagnostic Commands
```bash
# Check all services
systemctl status fleetpulse fleetpulse-chatbot

# Database diagnostics
sqlite3 fleetpulse.db ".tables"
sqlite3 fleetpulse.db "SELECT COUNT(*) FROM hosts;"

# Network diagnostics
netstat -tulpn | grep -E "(8000|8501)"
curl -v http://localhost:8000/api/fleet/status

# Resource monitoring
top
free -h
df -h
```

### Contact Information

For persistent issues or system-wide problems:
- **System Administrator**: Check service logs and configurations
- **Development Team**: Review error patterns and implement fixes
- **FleetPulse Support**: Backend service and API issues

## Future Enhancements

### Planned Features
- **Automated recovery scripts** for common failure scenarios
- **Predictive failure detection** based on performance trends
- **Integration with monitoring systems** (Prometheus, Grafana)
- **Advanced circuit breaker patterns** for service resilience
- **Machine learning-based error prediction** and prevention

### Feedback and Improvements

The diagnostic and error handling system continues to evolve based on:
- **User feedback** on error clarity and recovery effectiveness
- **System performance data** from production deployments
- **Error pattern analysis** for proactive improvements
- **Integration requirements** with existing monitoring infrastructure

---

This enhanced error handling and diagnostic system ensures that MCP tool failures are quickly identified, clearly communicated, and effectively resolved, maintaining the reliability and usability of the FleetPulse chatbot platform.
