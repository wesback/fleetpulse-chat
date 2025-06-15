"""Helper utilities for FleetPulse chatbot."""

import asyncio
import logging
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import streamlit as st


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up application logging."""
    logger = logging.getLogger("fleetpulse_chat")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def async_to_sync(async_func):
    """Decorator to run async functions in sync context."""
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(async_func(*args, **kwargs))
    
    return wrapper


def cache_result(ttl_seconds: int = 300):
    """Cache function results with TTL."""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = hashlib.md5(
                json.dumps([args, kwargs], sort_keys=True, default=str).encode()
            ).hexdigest()
            
            now = time.time()
            
            # Check if cached result is still valid
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            
            # Clean old entries
            cache_cleanup(cache, now, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def cache_cleanup(cache: Dict, current_time: float, ttl: int):
    """Clean expired entries from cache."""
    expired_keys = [
        key for key, (_, timestamp) in cache.items()
        if current_time - timestamp >= ttl
    ]
    
    for key in expired_keys:
        del cache[key]


def format_timestamp(timestamp: Union[str, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp for display."""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return timestamp
    
    if isinstance(timestamp, datetime):
        return timestamp.strftime(format_str)
    
    return str(timestamp)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def format_bytes(bytes_value: int, decimal_places: int = 2) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.{decimal_places}f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.{decimal_places}f} PB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_mentioned_hosts(text: str) -> List[str]:
    """Extract hostnames mentioned in text."""
    import re
    
    # Pattern for hostnames (simplified)
    hostname_pattern = r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\b'
    
    matches = re.findall(hostname_pattern, text)
    # Filter out common words that might match the pattern
    common_words = {'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'how', 'what', 'who', 'why'}
    
    hostnames = []
    for match in matches:
        hostname = match[0] if isinstance(match, tuple) else match
        if '.' in hostname and hostname.lower() not in common_words:
            hostnames.append(hostname)
    
    return list(set(hostnames))  # Remove duplicates


def extract_package_names(text: str) -> List[str]:
    """Extract package names mentioned in text."""
    import re
    
    # Common package name patterns
    patterns = [
        r'\b[a-zA-Z0-9][a-zA-Z0-9\-\.\+]*\b',  # General package pattern
        r'(?:apache2|nginx|mysql|postgresql|redis|docker|kubernetes|ansible)',  # Common packages
    ]
    
    packages = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        packages.extend(matches)
    
    # Filter common words
    common_words = {'and', 'or', 'but', 'the', 'is', 'are', 'was', 'were', 'have', 'has', 'had'}
    packages = [pkg for pkg in packages if pkg.lower() not in common_words]
    
    return list(set(packages))


def parse_natural_language_time(time_str: str) -> Optional[datetime]:
    """Parse natural language time expressions."""
    import re
    from datetime import datetime, timedelta
    
    now = datetime.now()
    time_str = time_str.lower().strip()
    
    # Relative time patterns
    patterns = {
        r'(\d+)\s*minutes?\s*ago': lambda m: now - timedelta(minutes=int(m.group(1))),
        r'(\d+)\s*hours?\s*ago': lambda m: now - timedelta(hours=int(m.group(1))),
        r'(\d+)\s*days?\s*ago': lambda m: now - timedelta(days=int(m.group(1))),
        r'yesterday': lambda m: now - timedelta(days=1),
        r'last\s*week': lambda m: now - timedelta(weeks=1),
        r'last\s*month': lambda m: now - timedelta(days=30),
        r'(\d+)\s*weeks?\s*ago': lambda m: now - timedelta(weeks=int(m.group(1))),
    }
    
    for pattern, func in patterns.items():
        match = re.search(pattern, time_str)
        if match:
            return func(match)
    
    # Try to parse ISO format
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    
    return None


def generate_conversation_title(first_message: str, max_length: int = 50) -> str:
    """Generate a conversation title from the first message."""
    # Remove common prefixes
    prefixes_to_remove = [
        "can you", "could you", "please", "help me", "i need", "how do i",
        "what is", "what are", "tell me", "show me", "explain"
    ]
    
    title = first_message.lower().strip()
    
    for prefix in prefixes_to_remove:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
            break
    
    # Capitalize first letter
    title = title.capitalize()
    
    # Truncate and clean up
    title = truncate_text(title, max_length, "...")
    
    # Remove trailing punctuation
    title = title.rstrip('.,!?;:')
    
    return title or "New Conversation"


def check_system_health() -> Dict[str, bool]:
    """Check health of system components."""
    health = {
        "database": True,  # Would check database connectivity
        "ai_provider": True,  # Would check AI provider connectivity
        "mcp_client": True,  # Would check MCP client connectivity
        "fleetpulse_api": True,  # Would check FleetPulse API connectivity
    }
    
    # TODO: Implement actual health checks
    return health


def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate token count for text."""
    # Rough estimation: 1 token ≈ 4 characters for English text
    # This is a simplification; actual tokenization depends on the model
    base_estimate = len(text) // 4
    
    # Adjust for different models
    model_adjustments = {
        "gpt-4": 1.0,
        "gpt-3.5-turbo": 1.0,
        "claude": 1.1,
        "gemini": 0.9,
    }
    
    adjustment = model_adjustments.get(model, 1.0)
    return int(base_estimate * adjustment)


def calculate_cost_estimate(tokens: int, provider: str, model: str = None) -> float:
    """Calculate estimated cost for token usage."""
    # Cost per 1K tokens (approximate pricing as of 2024)
    pricing = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        },
        "anthropic": {
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        },
        "google": {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
        }
    }
    
    if provider not in pricing:
        return 0.0
    
    provider_pricing = pricing[provider]
    model_pricing = provider_pricing.get(model or list(provider_pricing.keys())[0])
    
    if not model_pricing:
        return 0.0
    
    # Assume 50/50 split for input/output tokens
    input_tokens = tokens * 0.5
    output_tokens = tokens * 0.5
    
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    
    return input_cost + output_cost


def export_conversation_data(conversation_data: Dict[str, Any], format: str = "json") -> str:
    """Export conversation data in specified format."""
    if format == "json":
        return json.dumps(conversation_data, indent=2, default=str)
    
    elif format == "markdown":
        output = f"# {conversation_data.get('title', 'Conversation')}\n\n"
        output += f"**Created:** {conversation_data.get('created_at', 'Unknown')}\n"
        output += f"**Provider:** {conversation_data.get('provider', 'Unknown')}\n\n"
        
        for msg in conversation_data.get('messages', []):
            role = msg.get('role', 'unknown').title()
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            output += f"## {role}\n"
            if timestamp:
                output += f"*{timestamp}*\n\n"
            output += f"{content}\n\n"
        
        return output
    
    elif format == "text":
        output = f"Conversation: {conversation_data.get('title', 'Untitled')}\n"
        output += f"Created: {conversation_data.get('created_at', 'Unknown')}\n"
        output += f"Provider: {conversation_data.get('provider', 'Unknown')}\n"
        output += "=" * 50 + "\n\n"
        
        for msg in conversation_data.get('messages', []):
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            output += f"[{timestamp}] {role}:\n{content}\n\n"
        
        return output
    
    return str(conversation_data)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON with fallback."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Recursively merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def debounce(wait_time: float):
    """Debounce decorator for functions."""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if current_time - last_called[0] >= wait_time:
                last_called[0] = current_time
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_api_call(func_name: str, *args, **kwargs):
    """Cached wrapper for API calls."""
    # This would be used with specific API functions
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    
                    await asyncio.sleep(delay * (backoff ** attempt))
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    
                    time.sleep(delay * (backoff ** attempt))
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator