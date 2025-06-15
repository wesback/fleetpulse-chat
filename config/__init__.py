"""Configuration management for FleetPulse GenAI Chatbot."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum


class GenAIProvider(str, Enum):
    """Supported GenAI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # GenAI Provider Configuration
    genai_provider: GenAIProvider = Field(default=GenAIProvider.OPENAI, env="GENAI_PROVIDER")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    azure_openai_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    
    # FleetPulse Integration
    fleetpulse_api_url: str = Field(default="http://localhost:8000", env="FLEETPULSE_API_URL")
    fleetpulse_mcp_server: str = Field(default="./fleetpulse-mcp", env="FLEETPULSE_MCP_SERVER")
    
    # Application Configuration
    streamlit_server_port: int = Field(default=8501, env="STREAMLIT_SERVER_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_debug: bool = Field(default=False, env="ENABLE_DEBUG")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///fleetpulse_chat.db", env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


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