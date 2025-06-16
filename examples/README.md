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
User: What hosts do I have in my fleet and when were they last updated?

Chatbot: I'll check your FleetPulse data for current host information.

[Uses list_hosts MCP tool]

Based on your FleetPulse data, you have 5 hosts in your fleet:

1. **web-01.example.com**
   - OS: Ubuntu 22.04 LTS
   - Last Update: 2024-01-15
   - Total Packages: 1,234

2. **web-02.example.com** 
   - OS: Ubuntu 22.04 LTS
   - Last Update: 2024-01-14
   - Total Packages: 1,245

[... additional hosts ...]

Would you like me to show recent update activity for any specific host?
```

### Package Update History
```
User: What packages were updated on web-01 in the last week?

Chatbot: Let me check the recent update reports for web-01.

[Uses get_host_reports MCP tool with hostname="web-01" and days=7]

Here are the package updates for web-01 in the last 7 days:

**January 15, 2024:**
- nginx: 1.18.0 → 1.20.1 (security update)
- openssl: 1.1.1f → 1.1.1w (security update)
- curl: 7.68.0 → 7.81.0 (regular update)

**January 12, 2024:**
- python3: 3.8.10 → 3.8.16 (security update)
- git: 2.25.1 → 2.34.1 (feature update)

The security updates for nginx and openssl are particularly important - good to see these were applied promptly!
```

### Package Search
```
User: Do I have nginx installed anywhere and what versions?

Chatbot: I'll search for nginx packages across your fleet.

[Uses search MCP tool with query="nginx"]

Found nginx installations across your fleet:

**web-01.example.com**: nginx 1.20.1 (updated Jan 15)
**web-02.example.com**: nginx 1.20.1 (updated Jan 15) 
**lb-01.example.com**: nginx 1.18.0 (needs update!)

It looks like lb-01 is running an older version. The other hosts are up to date with version 1.20.1.
```