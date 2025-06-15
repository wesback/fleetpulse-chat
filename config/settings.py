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


class AppSettings(BaseSettings):
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False