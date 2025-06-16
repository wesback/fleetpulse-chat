"""
Test expert routing functionality.

This script demonstrates how the intelligent expert routing works
by testing various user queries and showing which expert gets selected.
"""

import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import from the app
sys.path.append(str(Path(__file__).parent.parent))

from core.expert_router import ExpertRouter, ExpertType


def test_expert_routing():
    """Test the expert routing with various sample queries."""
    router = ExpertRouter()
    
    # Test queries with expected experts
    test_cases = [
        # Linux Admin queries
        ("How do I check disk space on my servers?", ExpertType.LINUX_ADMIN),
        ("Can you help me troubleshoot systemd service issues?", ExpertType.LINUX_ADMIN),
        ("What does 'ps aux' show me?", ExpertType.LINUX_ADMIN),
        ("How to configure iptables firewall rules?", ExpertType.LINUX_ADMIN),
        
        # Ansible queries
        ("Write an Ansible playbook to install nginx", ExpertType.ANSIBLE),
        ("How do I use Jinja2 templates in Ansible?", ExpertType.ANSIBLE),
        ("Best practices for Ansible role organization", ExpertType.ANSIBLE),
        ("Debug failed Ansible tasks", ExpertType.ANSIBLE),
        
        # Update Management queries
        ("Schedule updates for my fleet", ExpertType.UPDATES),
        ("What's the rollback strategy if updates fail?", ExpertType.UPDATES),
        ("Show me pending security patches", ExpertType.UPDATES),
        ("How to do canary deployments for updates?", ExpertType.UPDATES),
        
        # FleetPulse queries
        ("Get the status of all hosts in FleetPulse", ExpertType.FLEETPULSE),
        ("FleetPulse API is returning errors", ExpertType.FLEETPULSE),
        ("Generate a fleet report", ExpertType.FLEETPULSE),
        ("How to check FleetPulse backend health?", ExpertType.FLEETPULSE),
        
        # General queries
        ("Hello, how are you?", ExpertType.GENERAL),
        ("What can you help me with?", ExpertType.GENERAL),
        ("Tell me about cloud computing", ExpertType.GENERAL),
    ]
    
    print("🎯 Expert Routing Test Results")
    print("=" * 50)
    
    correct_predictions = 0
    total_predictions = len(test_cases)
    
    for query, expected_expert in test_cases:
        result = router.route_query(query)
        
        # Check if prediction is correct
        is_correct = result.expert_type == expected_expert
        if is_correct:
            correct_predictions += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"\n{status} Query: \"{query}\"")
        print(f"   Expected: {expected_expert.value}")
        print(f"   Got: {result.expert_type.value} (confidence: {result.confidence:.1%})")
        
        if result.keywords_matched:
            print(f"   Keywords: {', '.join(result.keywords_matched[:3])}...")
        
        if not is_correct:
            print(f"   Reasoning: {result.reasoning}")
    
    print("\n" + "=" * 50)
    accuracy = correct_predictions / total_predictions
    print(f"🎯 Accuracy: {correct_predictions}/{total_predictions} ({accuracy:.1%})")
    
    if accuracy < 0.8:
        print("⚠️  Consider tuning keyword weights or adding more patterns")
    else:
        print("✅ Routing accuracy looks good!")


def test_context_routing():
    """Test routing with conversation context."""
    router = ExpertRouter()
    
    print("\n\n🔄 Context-Aware Routing Test")
    print("=" * 50)
    
    # Simulate a conversation about Ansible
    conversation_history = [
        {"role": "user", "content": "How do I write an Ansible playbook?"},
        {"role": "assistant", "content": "I'll help you create an Ansible playbook..."},
        {"role": "user", "content": "Thanks! Now I need to add handlers."}
    ]
    
    # This query is ambiguous but should route to Ansible due to context
    result = router.route_query(
        "How do I add error handling?",
        conversation_history=conversation_history
    )
    
    print(f"Query: \"How do I add error handling?\"")
    print(f"Expert: {result.expert_type.value} (confidence: {result.confidence:.1%})")
    print(f"Reasoning: {result.reasoning}")
    
    if result.context_factors:
        print("Context factors:")
        for factor in result.context_factors:
            print(f"  - {factor}")


def test_low_confidence_suggestions():
    """Test alternative suggestions for low-confidence queries."""
    router = ExpertRouter()
    
    print("\n\n🤔 Low Confidence Alternatives Test")
    print("=" * 50)
    
    # Ambiguous query that could match multiple experts
    ambiguous_query = "How do I check server performance?"
    
    result = router.route_query(ambiguous_query)
    alternatives = router.suggest_alternatives(ambiguous_query, result)
    
    print(f"Query: \"{ambiguous_query}\"")
    print(f"Primary: {result.expert_type.value} (confidence: {result.confidence:.1%})")
    
    if alternatives:
        print("Alternatives:")
        for alt in alternatives:
            print(f"  - {alt.expert_type.value} (confidence: {alt.confidence:.1%})")
            print(f"    Reasoning: {alt.reasoning}")


if __name__ == "__main__":
    test_expert_routing()
    test_context_routing()
    test_low_confidence_suggestions()
