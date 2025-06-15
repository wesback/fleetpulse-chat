"""
Example conversation scenarios for FleetPulse GenAI Chatbot
"""

# Example 1: Fleet Status Check
example_conversations = {
    "fleet_status": {
        "user": "What's the current status of my fleet?",
        "assistant": "I'll check your fleet status for you. Let me gather the current information...",
        "tools_used": ["get_fleet_status"],
        "expert_mode": "fleetpulse"
    },
    
    "security_updates": {
        "user": "Show me all hosts with critical security updates",
        "assistant": "I'll search for hosts with critical security updates. This is important for maintaining fleet security...",
        "tools_used": ["get_pending_updates"],
        "expert_mode": "updates"
    },
    
    "ansible_playbook": {
        "user": "Help me create an Ansible playbook to update all web servers",
        "assistant": "I'll help you create a comprehensive Ansible playbook for updating web servers...",
        "tools_used": [],
        "expert_mode": "ansible"
    },
    
    "host_details": {
        "user": "Give me detailed information about web-server-01.example.com",
        "assistant": "Let me retrieve detailed information about that host for you...",
        "tools_used": ["get_host_details"],
        "expert_mode": "linux_admin"
    }
}

# Configuration examples
config_examples = {
    "minimal": {
        "GENAI_PROVIDER": "openai",
        "OPENAI_API_KEY": "sk-your-key-here",
        "FLEETPULSE_API_URL": "http://localhost:8000"
    },
    
    "production": {
        "GENAI_PROVIDER": "openai",
        "OPENAI_API_KEY": "sk-your-production-key",
        "FLEETPULSE_API_URL": "https://fleetpulse.company.com",
        "LOG_LEVEL": "WARNING",
        "ENABLE_DEBUG": "false",
        "SECRET_KEY": "your-production-secret-key"
    },
    
    "multi_provider": {
        "GENAI_PROVIDER": "anthropic",
        "OPENAI_API_KEY": "sk-openai-key",
        "ANTHROPIC_API_KEY": "sk-ant-api03-anthropic-key",
        "GOOGLE_API_KEY": "google-api-key",
        "FLEETPULSE_API_URL": "http://localhost:8000"
    }
}

if __name__ == "__main__":
    print("FleetPulse GenAI Chatbot Examples")
    print("=================================")
    
    print("\nExample Conversations:")
    for name, example in example_conversations.items():
        print(f"\n{name.upper()}:")
        print(f"User: {example['user']}")
        print(f"Mode: {example['expert_mode']}")
        print(f"Tools: {example['tools_used']}")
    
    print("\nConfiguration Examples:")
    for name, config in config_examples.items():
        print(f"\n{name.upper()} CONFIG:")
        for key, value in config.items():
            print(f"{key}={value}")