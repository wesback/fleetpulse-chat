# FleetPulse GenAI Chatbot - Usage Examples

This directory contains example usage scenarios and configuration examples for the FleetPulse GenAI Chatbot.

## 🚀 Quick Start Example

### 1. Basic Setup

```bash
# Clone the repository
git clone https://github.com/wesback/fleetpulse-chat.git
cd fleetpulse-chat

# Copy environment configuration
cp .env.example .env

# Edit with your API keys
nano .env
```

### 2. Configuration Example

```bash
# .env file configuration
GENAI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
FLEETPULSE_API_URL=http://localhost:8000
LOG_LEVEL=INFO
```

### 3. Docker Deployment

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f fleetpulse-chat

# Access the application
open http://localhost:8501
```

## 💬 Example Conversations

### Fleet Status Inquiry
```
User: What's the current status of my fleet?