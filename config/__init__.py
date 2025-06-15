"""Configuration management for FleetPulse GenAI Chatbot."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
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


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields instead of forbidding them
    )
    
    # GenAI Provider Configuration
    genai_provider: GenAIProvider = GenAIProvider.OPENAI
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # FleetPulse Integration
    fleetpulse_api_url: str = "http://localhost:8000"
    fleetpulse_mcp_server: str = "./fleetpulse-mcp"
    
    # MCP Configuration
    mcp_connection_type: MCPConnectionType = MCPConnectionType.HTTP
    mcp_server_url: Optional[str] = None
    mcp_timeout: int = 30
    mcp_max_retries: int = 3
    
    # Application Configuration
    streamlit_server_port: int = 8501
    log_level: str = "INFO"
    enable_debug: bool = False
    
    # Database Configuration
    database_url: str = "sqlite:///fleetpulse_chat.db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Optional Features
    redis_url: Optional[str] = None
    enable_experimental_features: bool = False
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    
    # Model Defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 2000


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def validate_provider_config(provider: GenAIProvider) -> bool:
    """Validate that required configuration exists for the specified provider."""
    if provider == GenAIProvider.OPENAI:
        return bool(settings.openai_api_key)
    elif provider == GenAIProvider.ANTHROPIC:
        return bool(settings.anthropic_api_key)
    elif provider == GenAIProvider.GOOGLE:
        return bool(settings.google_api_key)
    elif provider == GenAIProvider.AZURE:
        return bool(settings.azure_openai_key and settings.azure_openai_endpoint)
    elif provider == GenAIProvider.OLLAMA:
        return bool(settings.ollama_base_url)
    return False


def get_available_providers() -> List[GenAIProvider]:
    """Get list of providers that have valid configuration."""
    available = []
    for provider in GenAIProvider:
        if validate_provider_config(provider):
            available.append(provider)
    return available