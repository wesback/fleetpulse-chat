# FleetPulse GenAI Chatbot

A comprehensive Streamlit application that serves as an intelligent chatbot for FleetPulse fleet management. The application integrates multiple GenAI APIs and leverages the Model Context Protocol (MCP) for enhanced functionality.

## 🚀 Features

- **Multi-Provider AI Support**: OpenAI, Anthropic, Google Gemini, Azure OpenAI, and Ollama
- **Microsoft Semantic Kernel Integration**: Unified AI orchestration across providers
- **Model Context Protocol (MCP)**: Direct integration with FleetPulse backend
- **Expert System Prompts**: Specialized modes for Linux, Ansible, Updates, and FleetPulse operations
- **Interactive Dashboard**: Real-time fleet status visualization
- **Conversation Management**: Persistent chat history with SQLite
- **Tool Integration**: Automated tool detection and execution
- **Docker Deployment**: Complete containerization with docker-compose

## 📋 Requirements

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- At least one configured AI provider (OpenAI, Anthropic, Google, Azure, or Ollama)
- Access to FleetPulse backend API

## 🔧 Installation

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wesback/fleetpulse-chat.git
   cd fleetpulse-chat
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

### Docker Deployment

1. **Using docker-compose (recommended):**
   ```bash
   # Clone and configure
   git clone https://github.com/wesback/fleetpulse-chat.git
   cd fleetpulse-chat
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your settings
   
   # Start services
   docker-compose up -d
   ```

2. **Using Docker directly:**
   ```bash
   # Build image
   docker build -t fleetpulse-chat .
   
   # Run container
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=your_key \
     -e FLEETPULSE_API_URL=http://localhost:8000 \
     fleetpulse-chat
   ```

## ⚙️ Configuration

### Environment Variables

#### Required (at least one AI provider)
```bash
# AI Provider Selection
GENAI_PROVIDER=openai  # openai, anthropic, google, azure, ollama

# AI Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-1.5-flash  # Optional: gemini-1.5-flash, gemini-1.5-pro, gemini-1.0-pro
AZURE_OPENAI_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT_NAME=gpt-4  # Optional: your Azure OpenAI deployment name
```

#### Optional
```bash
# FleetPulse Integration
FLEETPULSE_API_URL=http://localhost:8000
FLEETPULSE_MCP_SERVER=./fleetpulse-mcp

# Application Settings
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
ENABLE_DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///fleetpulse_chat.db

# Local AI (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
```

### AI Provider Setup

#### OpenAI
1. Get API key from https://platform.openai.com/api-keys
2. Set `OPENAI_API_KEY=sk-your-key`

#### Anthropic
1. Get API key from https://console.anthropic.com/
2. Set `ANTHROPIC_API_KEY=sk-ant-api03-your-key`

#### Google Gemini
1. Get API key from https://makersuite.google.com/app/apikey
2. Set `GOOGLE_API_KEY=your-key`

#### Azure OpenAI
1. Set up Azure OpenAI resource
2. Set `AZURE_OPENAI_KEY=your-key` and `AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/`

#### Ollama (Local)
1. Install Ollama: https://ollama.ai/
2. Start Ollama service: `ollama serve`
3. Pull a model: `ollama pull llama2`
4. Set `OLLAMA_BASE_URL=http://localhost:11434`

## 🎯 Usage

### Getting Started

1. **Access the application** at http://localhost:8501
2. **Select an AI Provider** from the dropdown
3. **Choose an Expert Mode** based on your needs:
   - **General Assistant**: Multi-purpose FleetPulse helper
   - **Linux System Admin**: Package management and system operations
   - **Ansible Automation**: Playbook development and automation
   - **Package Update Manager**: Fleet update coordination
   - **FleetPulse Operations**: Platform-specific operations

4. **Start chatting** with questions like:
   - "What's the current status of my fleet?"
   - "Show me hosts with pending security updates"
   - "Help me create an Ansible playbook for package updates"
   - "Generate a fleet compliance report"

### Expert Modes

#### 🐧 Linux System Admin
Specialized for:
- Package management across distributions (apt, yum, dnf, pacman)
- System monitoring and troubleshooting
- Security hardening and best practices
- Performance optimization

#### ⚙️ Ansible Automation
Expert in:
- Playbook development and best practices
- Inventory management
- Role creation and Galaxy usage
- CI/CD integration

#### 📦 Package Update Manager
Focused on:
- Fleet-wide update coordination
- Risk assessment and rollback strategies
- Compliance and security patch management
- Update scheduling and automation

#### 🚀 FleetPulse Operations
Specialized for:
- FleetPulse API operations
- Fleet monitoring and reporting
- Update orchestration
- Troubleshooting platform issues

### Available Tools

The chatbot automatically detects when to use these FleetPulse tools:

- **get_fleet_status()**: Overall fleet health summary
- **get_host_details(hostname)**: Detailed host information
- **get_update_history(hostname, days)**: Package update history
- **get_pending_updates(severity)**: Systems with available updates
- **schedule_updates(hostnames, schedule)**: Schedule update operations
- **generate_fleet_report(format)**: Comprehensive fleet reports
- **get_system_metrics(hostname)**: Performance metrics
- **check_package_info(package_name)**: Package information

### Dashboard Features

Toggle the interactive dashboard to view:
- Fleet status overview with health metrics
- Host distribution charts
- Update status visualization
- System performance metrics
- Compliance summaries

## 🏗️ Architecture

### Core Components

```
fleetpulse-chatbot/
├── app.py                    # Main Streamlit application
├── config/
│   ├── __init__.py          # Configuration management
│   ├── settings.py          # Settings with environment variables
│   └── prompts.py           # System prompt definitions
├── core/
│   ├── genai_manager.py     # Multi-provider AI coordination
│   ├── mcp_client.py        # Model Context Protocol integration
│   └── conversation.py      # Chat history management
├── ui/
│   ├── components.py        # Custom Streamlit components
│   └── dashboard.py         # Fleet dashboard integration
├── utils/
│   ├── validators.py        # Input validation utilities
│   └── helpers.py           # Helper functions
└── tests/                   # Test suite
```

### Data Flow

1. **User Input** → Streamlit UI
2. **Message Processing** → GenAI Manager
3. **Tool Detection** → MCP Client
4. **FleetPulse Integration** → Backend API
5. **AI Response** → Selected Provider (OpenAI/Anthropic/etc.)
6. **Response Display** → Streamlit UI
7. **Conversation Storage** → SQLite Database

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=. tests/

# Specific test categories
pytest tests/test_genai.py -v
pytest tests/test_mcp.py -v
pytest tests/test_ui.py -v
```

## 🔒 Security

### Best Practices

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use secure secret management in production
3. **Input Validation**: All user inputs are sanitized
4. **Rate Limiting**: Built-in protection against API abuse
5. **Docker Secrets**: Use Docker secrets for sensitive data in production

### Production Deployment

```bash
# Use Docker secrets
echo "your-openai-key" | docker secret create openai_api_key -

# Update docker-compose.yml to use secrets
services:
  fleetpulse-chat:
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
```

## 📊 Monitoring

### Health Checks

- Application health: `http://localhost:8501/_stcore/health`
- Component status available in sidebar
- Docker health checks included

### Logging

Logs are available at different levels:
```bash
# Set log level
export LOG_LEVEL=DEBUG

# View logs
docker-compose logs -f fleetpulse-chat
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following the coding standards
4. Add tests for new functionality
5. Run tests: `pytest`
6. Submit a pull request

### Coding Standards

- Follow PEP 8 for Python code
- Use type hints for all functions
- Add docstrings for all modules, classes, and functions
- Implement comprehensive error handling
- Write tests for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**No AI providers available:**
- Verify at least one API key is configured
- Check API key format and validity
- Test connectivity to AI provider APIs

**FleetPulse connection failed:**
- Verify `FLEETPULSE_API_URL` is correct
- Check FleetPulse backend is running
- Verify network connectivity

**Database errors:**
- Ensure write permissions for database file
- Check disk space for SQLite database
- Verify database URL format

**Docker issues:**
- Check Docker and docker-compose versions
- Verify port availability (8501)
- Review container logs: `docker-compose logs`

### Getting Help

1. Check the [Issues](https://github.com/wesback/fleetpulse-chat/issues) page
2. Review logs for detailed error messages
3. Ensure all requirements are met
4. Test with minimal configuration first

## 🗺️ Roadmap

- [ ] Advanced conversation threading
- [ ] Custom tool development framework
- [ ] Integration with more monitoring systems
- [ ] Mobile-responsive UI improvements
- [ ] Advanced analytics and reporting
- [ ] Multi-tenant support
- [ ] Plugin architecture
- [ ] Voice interface integration

## 📧 Support

For questions and support:
- GitHub Issues: https://github.com/wesback/fleetpulse-chat/issues
- Documentation: This README and inline code documentation
- Examples: See the `/examples` directory for usage scenarios