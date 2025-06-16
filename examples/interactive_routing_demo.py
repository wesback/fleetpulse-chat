"""
Interactive Expert Routing Demo

This script provides an interactive demonstration of the intelligent
expert routing system, allowing users to see how different queries
are automatically routed to appropriate experts.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from the app
sys.path.append(str(Path(__file__).parent.parent))

from core.expert_router import ExpertRouter


def interactive_demo():
    """Run an interactive demonstration of expert routing."""
    router = ExpertRouter()
    
    print("🎯 FleetPulse Intelligent Expert Routing Demo")
    print("=" * 50)
    print("Type your questions and see which expert gets selected!")
    print("Type 'quit' to exit, 'examples' to see sample queries.")
    print()
    
    while True:
        try:
            user_input = input("💬 Your query: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for trying the expert routing demo!")
                break
            
            if user_input.lower() == 'examples':
                show_examples()
                continue
            
            if not user_input:
                continue
            
            # Route the query
            result = router.route_query(user_input)
            
            # Display results
            print(f"\n🎯 Routing Result:")
            print(f"   Expert: {router.get_expert_description(result.expert_type)}")
            print(f"   Confidence: {result.confidence:.1%}")
            
            if result.confidence < 0.4:
                print(f"   ⚠️  Low confidence - showing alternatives")
                alternatives = router.suggest_alternatives(user_input, result)
                for alt in alternatives:
                    alt_desc = router.get_expert_description(alt.expert_type)
                    print(f"      Alternative: {alt_desc} ({alt.confidence:.1%})")
            
            if result.keywords_matched:
                keywords_display = ", ".join(result.keywords_matched[:5])
                if len(result.keywords_matched) > 5:
                    keywords_display += f" (and {len(result.keywords_matched) - 5} more)"
                print(f"   Keywords: {keywords_display}")
            
            print(f"   Reasoning: {result.reasoning}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Thanks for trying the expert routing demo!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()


def show_examples():
    """Show example queries for each expert type."""
    examples = {
        "🐧 Linux System Admin": [
            "How do I check disk space?",
            "Troubleshoot systemd service",
            "Configure iptables firewall",
            "What does 'ps aux' show?"
        ],
        "⚙️ Ansible Automation": [
            "Write an Ansible playbook",
            "Use Jinja2 templates",
            "Organize Ansible roles",
            "Debug failed tasks"
        ],
        "📦 Package Update Manager": [
            "Schedule fleet updates",
            "Rollback strategy for patches",
            "Show pending security updates",
            "Canary deployment process"
        ],
        "🚀 FleetPulse Operations": [
            "Get fleet status",
            "Generate fleet report",
            "FleetPulse API errors",
            "Check backend health"
        ],
        "🤖 General Assistant": [
            "Hello, how are you?",
            "What can you help with?",
            "Tell me about cloud computing"
        ]
    }
    
    print("\n📚 Example Queries by Expert:")
    print("=" * 40)
    
    for expert, queries in examples.items():
        print(f"\n{expert}:")
        for query in queries:
            print(f"   • {query}")
    
    print()


if __name__ == "__main__":
    interactive_demo()
