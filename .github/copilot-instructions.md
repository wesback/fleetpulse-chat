# Copilot Instructions for FleetPulse GenAI Chatbot

## Project Context
This is a Streamlit application that serves as an intelligent chatbot for FleetPulse fleet management. FleetPulse is a lightweight dashboard to monitor and audit Linux package updates across server fleets. The chatbot integrates multiple GenAI APIs and leverages Model Context Protocol (MCP) tools for enhanced fleet management capabilities.

## Core Architecture
- **Frontend**: Streamlit web application with chat interface
- **AI Orchestration**: Microsoft Semantic Kernel for multi-provider coordination
- **Backend Integration**: FleetPulse FastAPI backend (port 8000) via MCP tools
- **Data Storage**: SQLite database for conversation history and configurations
- **Deployment**: Docker containers with environment-based configuration

## Technology Stack
- **UI Framework**: Streamlit with custom components
- **AI Coordination**: Microsoft Semantic Kernel
- **GenAI Providers**: OpenAI, Anthropic, Google Gemini, Azure OpenAI, Ollama
- **MCP Integration**: Model Context Protocol client for FleetPulse tools
- **Backend**: FastAPI (FleetPulse backend)
- **Database**: SQLite for app data, FleetPulse uses its own SQLite
- **Containerization**: Docker with docker-compose

## File Structure Conventions
```
fleetpulse-chatbot/
├── app.py                    # Main Streamlit application
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuration management
│   └── prompts.py           # System prompt definitions
├── core/
│   ├── __init__.py
│   ├── genai_manager.py     # AI provider coordination
│   ├── mcp_client.py        # MCP integration
│   └── conversation.py      # Chat history management
├── ui/
│   ├── __init__.py
│   ├── components.py        # Custom Streamlit components
│   └── dashboard.py         # Fleet dashboard integration
├── utils/
│   ├── __init__.py
│   ├── validators.py        # Input validation
│   └── helpers.py           # Utility functions
├── tests/
│   ├── test_genai.py
│   ├── test_mcp.py
│   └── test_ui.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Environment Variables
Always use these environment variable patterns:
```bash
# GenAI Provider Selection
GENAI_PROVIDER=openai  # openai, anthropic, google, azure, ollama

# API Keys (use secure defaults)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
GOOGLE_API_KEY=${GOOGLE_API_KEY:-}
AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY:-}
AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT:-}
OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}

# FleetPulse Integration
FLEETPULSE_API_URL=${FLEETPULSE_API_URL:-http://localhost:8000}
FLEETPULSE_MCP_SERVER=${FLEETPULSE_MCP_SERVER:-./fleetpulse-mcp}

# Application Configuration
STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}
LOG_LEVEL=${LOG_LEVEL:-INFO}
ENABLE_DEBUG=${ENABLE_DEBUG:-false}
```

## Code Style Guidelines

### Python Code Standards
- Use **async/await** for all AI API calls and MCP operations
- Implement **type hints** for all function parameters and returns
- Use **dataclasses** or **Pydantic models** for structured data
- Follow **PEP 8** naming conventions
- Use **f-strings** for string formatting
- Implement **comprehensive error handling** with specific exception types

### Streamlit Best Practices
- Use **st.session_state** for persistent data across reruns
- Implement **st.cache_data** for expensive operations
- Use **st.columns()** for responsive layouts
- Implement **custom components** in separate files
- Use **st.sidebar** for configuration controls
- Implement **progress indicators** for long-running operations

### AI Integration Patterns
- Always use **Semantic Kernel** as the orchestration layer
- Implement **fallback providers** for reliability
- Use **streaming responses** when available
- Implement **token counting** and **cost tracking**
- Cache **model responses** appropriately
- Implement **rate limiting** for API calls

## Specific Implementation Guidelines

### GenAI Provider Integration
```python
# Always implement this interface for consistency
class AIProvider:
    async def chat_completion(self, messages: List[dict], **kwargs) -> str:
        """Standard interface for all providers"""
        pass
    
    async def stream_completion(self, messages: List[dict], **kwargs) -> AsyncIterator[str]:
        """Streaming interface"""
        pass
```

### MCP Tool Implementation
- Use **standardized tool schemas** for all MCP operations
- Implement **async tool calls** with proper error handling
- Cache **tool results** when appropriate
- Provide **clear tool descriptions** for AI context
- Implement **parameter validation** for all tools

### System Prompts
Create specialized prompts for these domains:
- **Linux System Administration**: Package management, monitoring, troubleshooting
- **Ansible Automation**: Playbooks, roles, inventory management
- **Fleet Management**: Update coordination, risk assessment, reporting
- **FleetPulse Operations**: API usage, data interpretation, troubleshooting

### Error Handling
- Use **specific exception classes** for different error types
- Implement **graceful degradation** when services are unavailable
- Provide **user-friendly error messages** in the UI
- Log **detailed error information** for debugging
- Implement **retry logic** with exponential backoff

### Security Considerations
- **Never log API keys** or sensitive information
- Validate **all user inputs** before processing
- Use **secure defaults** for configuration
- Implement **rate limiting** to prevent abuse
- Sanitize **data before display** in the UI

## FleetPulse Domain Knowledge
When generating code, always consider:
- **FleetPulse Architecture**: FastAPI backend, React frontend, SQLite database
- **Update Workflow**: Ansible playbooks → API reports → Dashboard display
- **Data Models**: Hosts, packages, update history, OS distributions
- **API Endpoints**: /report, /hosts, /history, /health
- **Observability**: OpenTelemetry integration with Jaeger
- **Deployment**: Docker compose with configurable modes

## UI/UX Requirements
- **Dark/Light Theme Toggle**: Use Streamlit's built-in theming
- **Responsive Design**: Mobile-friendly layouts
- **Loading States**: Show progress for long operations
- **Error States**: Clear error messages with recovery options
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Performance**: Minimize API calls and cache responses

## Testing Requirements
- **Unit Tests**: All core functionality with pytest
- **Integration Tests**: MCP tool interactions
- **UI Tests**: Critical user flows with Selenium
- **Mock Services**: For AI providers and FleetPulse backend
- **Performance Tests**: Load testing for concurrent users

## Documentation Standards
- **Docstrings**: Google-style for all functions and classes
- **Type Hints**: Complete type annotations
- **README**: Setup instructions, environment variables, usage examples
- **API Documentation**: Auto-generated with Sphinx
- **User Guide**: Step-by-step usage instructions

## Deployment Considerations
- **Docker Multi-stage**: Separate build and runtime stages
- **Health Checks**: Container health endpoints
- **Secrets Management**: Use Docker secrets or external providers
- **Scaling**: Stateless design for horizontal scaling
- **Monitoring**: Application metrics and logging
- **Backup**: Conversation history and configuration data

## AI Behavior Guidelines
When implementing AI interactions:
- **Context Awareness**: Always include FleetPulse context in prompts
- **Tool Usage**: Prefer MCP tools over generic responses when applicable
- **Expert Personas**: Switch between Linux/Ansible/Fleet management expertise
- **Conversation Flow**: Maintain context across multiple exchanges
- **Response Quality**: Prioritize accuracy over speed
- **Fallback Handling**: Graceful degradation when tools fail

## Performance Optimization
- **Lazy Loading**: Load AI providers only when needed
- **Connection Pooling**: Reuse HTTP connections
- **Response Caching**: Cache identical queries
- **Streaming**: Use streaming for long responses
- **Background Tasks**: Async processing for heavy operations
- **Memory Management**: Clean up resources properly

Remember: This chatbot is specifically designed for FleetPulse fleet management scenarios. Always prioritize functionality that helps users manage Linux systems, coordinate updates, and troubleshoot fleet-wide issues.