"""Settings configuration module."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from enum import Enum


class GenAIProvider(str, Enum):
    """Supported GenAI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    OLLAMA = "ollama"


class MCPConnectionType(str, Enum):
    """Supported MCP connection types."""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


class AppSettings(BaseSettings):
    """Application settings with environment variable support."""
    
    # GenAI Provider Configuration
    genai_provider: GenAIProvider = GenAIProvider.OPENAI
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # FleetPulse Integration (Legacy REST API)
    fleetpulse_api_url: str = "http://localhost:8000"
    
    # FastMCP Server Configuration
    mcp_connection_type: MCPConnectionType = MCPConnectionType.HTTP
    mcp_server_url: str = "http://localhost:8001"
    mcp_server_command: Optional[str] = None
    mcp_timeout: int = 30
    mcp_max_retries: int = 3
    
    # Application Configuration
    streamlit_server_port: int = 8501
    log_level: str = "INFO"
    enable_debug: bool = False
    
    # Database Configuration
    database_url: str = "sqlite:///fleetpulse_chat.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
_settings = None


def get_settings() -> AppSettings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def get_available_providers() -> list[GenAIProvider]:
    """Get list of available GenAI providers based on API keys."""
    settings = get_settings()
    providers = []
    
    if settings.openai_api_key:
        providers.append(GenAIProvider.OPENAI)
    if settings.anthropic_api_key:
        providers.append(GenAIProvider.ANTHROPIC)
    if settings.google_api_key:
        providers.append(GenAIProvider.GOOGLE)
    if settings.azure_openai_key and settings.azure_openai_endpoint:
        providers.append(GenAIProvider.AZURE)
    # Ollama is always available if the base URL is configured
    if settings.ollama_base_url:
        providers.append(GenAIProvider.OLLAMA)
    
    return providers