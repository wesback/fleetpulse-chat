"""Input validation utilities for FleetPulse chatbot."""

import re
from typing import Union, List, Optional, Dict, Any
from datetime import datetime
import ipaddress


def validate_hostname(hostname: str) -> bool:
    """Validate hostname format."""
    if not hostname or len(hostname) > 253:
        return False
    
    # Hostname regex pattern
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, hostname))


def validate_ip_address(ip: str) -> bool:
    """Validate IP address (IPv4 or IPv6)."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_package_name(package_name: str) -> bool:
    """Validate package name format."""
    if not package_name:
        return False
    
    # Basic package name pattern (alphanumeric, hyphens, dots, plus signs)
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.\+]*$'
    return bool(re.match(pattern, package_name))


def validate_severity_level(severity: str) -> bool:
    """Validate severity level."""
    valid_severities = ['critical', 'high', 'important', 'medium', 'moderate', 'low', 'minimal']
    return severity.lower() in valid_severities


def validate_update_type(update_type: str) -> bool:
    """Validate update type."""
    valid_types = ['security', 'all', 'specific', 'critical', 'recommended']
    return update_type.lower() in valid_types


def validate_iso_datetime(datetime_str: str) -> bool:
    """Validate ISO 8601 datetime format."""
    try:
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def validate_report_format(format: str) -> bool:
    """Validate report format."""
    valid_formats = ['json', 'html', 'pdf', 'csv', 'xml']
    return format.lower() in valid_formats


def validate_metric_types(metric_types: List[str]) -> bool:
    """Validate metric types list."""
    valid_metrics = ['cpu', 'memory', 'disk', 'network', 'load', 'io']
    return all(metric.lower() in valid_metrics for metric in metric_types)


def sanitize_input(user_input: str, max_length: int = 1000) -> str:
    """Sanitize user input for safety."""
    if not user_input:
        return ""
    
    # Remove potential XSS characters and limit length
    sanitized = re.sub(r'[<>"\']', '', user_input)
    return sanitized[:max_length].strip()


def validate_hostnames_list(hostnames: List[str]) -> Dict[str, List[str]]:
    """Validate a list of hostnames and return valid/invalid lists."""
    valid = []
    invalid = []
    
    for hostname in hostnames:
        if validate_hostname(hostname):
            valid.append(hostname)
        else:
            invalid.append(hostname)
    
    return {"valid": valid, "invalid": invalid}


def validate_port_number(port: Union[str, int]) -> bool:
    """Validate port number."""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_url(url: str) -> bool:
    """Validate URL format."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))


def validate_cron_expression(cron_expr: str) -> bool:
    """Validate cron expression format."""
    if not cron_expr:
        return False
    
    parts = cron_expr.split()
    if len(parts) != 5:
        return False
    
    # Basic validation for each field
    minute, hour, day, month, weekday = parts
    
    def validate_field(field: str, min_val: int, max_val: int) -> bool:
        if field == '*':
            return True
        
        # Handle ranges and lists
        for part in field.split(','):
            if '/' in part:
                range_part, step = part.split('/')
                if not step.isdigit():
                    return False
                part = range_part
            
            if '-' in part:
                start, end = part.split('-')
                if not (start.isdigit() and end.isdigit()):
                    return False
                if not (min_val <= int(start) <= max_val and min_val <= int(end) <= max_val):
                    return False
            elif part.isdigit():
                if not (min_val <= int(part) <= max_val):
                    return False
            elif part != '*':
                return False
        
        return True
    
    return (validate_field(minute, 0, 59) and
            validate_field(hour, 0, 23) and
            validate_field(day, 1, 31) and
            validate_field(month, 1, 12) and
            validate_field(weekday, 0, 7))


def validate_environment_variable(var_name: str, var_value: str) -> bool:
    """Validate environment variable name and value."""
    # Variable name should be uppercase letters, numbers, and underscores
    name_pattern = r'^[A-Z][A-Z0-9_]*$'
    if not re.match(name_pattern, var_name):
        return False
    
    # Value should not be empty and not contain certain characters
    if not var_value or '\n' in var_value or '\r' in var_value:
        return False
    
    return True


def validate_api_key(api_key: str, provider: str) -> bool:
    """Validate API key format for different providers."""
    if not api_key:
        return False
    
    patterns = {
        'openai': r'^sk-[a-zA-Z0-9]{48}$',
        'anthropic': r'^sk-ant-api[0-9]{2}-[a-zA-Z0-9\-_]{95}$',
        'google': r'^[a-zA-Z0-9\-_]{39}$',
        'azure': r'^[a-f0-9]{32}$'
    }
    
    pattern = patterns.get(provider.lower())
    if pattern:
        return bool(re.match(pattern, api_key))
    
    # Generic validation for unknown providers
    return len(api_key) > 10 and api_key.isalnum()


def validate_json_data(data: str) -> bool:
    """Validate JSON data format."""
    try:
        import json
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """Validate file path and extension."""
    if not file_path:
        return False
    
    # Check for path traversal attacks
    if '..' in file_path or file_path.startswith('/'):
        return False
    
    if allowed_extensions:
        extension = file_path.split('.')[-1].lower()
        return extension in [ext.lower() for ext in allowed_extensions]
    
    return True


def validate_pagination_params(page: Union[str, int], per_page: Union[str, int]) -> Dict[str, Union[int, bool]]:
    """Validate pagination parameters."""
    try:
        page_num = int(page)
        per_page_num = int(per_page)
        
        valid = (page_num > 0 and 1 <= per_page_num <= 100)
        
        return {
            "valid": valid,
            "page": max(1, page_num),
            "per_page": min(100, max(1, per_page_num))
        }
    except (ValueError, TypeError):
        return {"valid": False, "page": 1, "per_page": 20}


class ValidationError(Exception):
    """Custom validation error exception."""
    pass


def validate_mcp_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate MCP tool parameters based on tool requirements."""
    
    validation_rules = {
        "get_host_details": {
            "required": ["hostname"],
            "validators": {
                "hostname": validate_hostname
            }
        },
        "get_update_history": {
            "required": ["hostname"],
            "optional": ["days"],
            "validators": {
                "hostname": validate_hostname,
                "days": lambda x: isinstance(x, int) and 1 <= x <= 365
            }
        },
        "get_pending_updates": {
            "optional": ["severity"],
            "validators": {
                "severity": validate_severity_level
            }
        },
        "schedule_updates": {
            "required": ["hostnames", "schedule"],
            "optional": ["update_type"],
            "validators": {
                "hostnames": lambda x: isinstance(x, list) and all(validate_hostname(h) for h in x),
                "schedule": validate_iso_datetime,
                "update_type": validate_update_type
            }
        },
        "generate_fleet_report": {
            "optional": ["format", "include_history"],
            "validators": {
                "format": validate_report_format,
                "include_history": lambda x: isinstance(x, bool)
            }
        },
        "get_system_metrics": {
            "required": ["hostname"],
            "optional": ["metric_types"],
            "validators": {
                "hostname": validate_hostname,
                "metric_types": validate_metric_types
            }
        },
        "check_package_info": {
            "required": ["package_name"],
            "optional": ["hostname"],
            "validators": {
                "package_name": validate_package_name,
                "hostname": validate_hostname
            }
        }
    }
    
    rules = validation_rules.get(tool_name, {})
    required = rules.get("required", [])
    optional = rules.get("optional", [])
    validators = rules.get("validators", {})
    
    # Check required parameters
    for param in required:
        if param not in parameters:
            raise ValidationError(f"Missing required parameter: {param}")
    
    # Validate all parameters
    validated_params = {}
    for param, value in parameters.items():
        if param not in required and param not in optional:
            continue  # Skip unknown parameters
        
        if param in validators:
            if not validators[param](value):
                raise ValidationError(f"Invalid value for parameter {param}: {value}")
        
        validated_params[param] = value
    
    return validated_params