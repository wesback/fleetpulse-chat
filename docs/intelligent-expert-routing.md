# Intelligent Expert Routing System

## Overview

The FleetPulse chatbot now features an **intelligent expert routing system** that automatically determines the most appropriate expert based on user queries, eliminating the need for manual expert selection.

## Key Features

### 🎯 Automatic Expert Selection
- **Keyword Analysis**: Recognizes technical terms, commands, and domain-specific language
- **Context Patterns**: Uses regex patterns to detect code snippets and command structures
- **Conversation Context**: Considers previous messages for continuity
- **Confidence Scoring**: Provides transparency into routing decisions

### 🧠 Available Experts

| Expert | Icon | Specialization |
|--------|------|----------------|
| **General Assistant** | 🤖 | General questions, getting started, broad topics |
| **Linux System Admin** | 🐧 | System administration, package management, troubleshooting |
| **Ansible Automation** | ⚙️ | Playbooks, roles, automation, infrastructure as code |
| **Package Update Manager** | 📦 | Fleet updates, patch management, rollback strategies |
| **FleetPulse Operations** | 🚀 | FleetPulse API, dashboard, MCP tools, system diagnostics |

### 📊 Routing Algorithm

The system uses a multi-factor scoring approach:

1. **Primary Keywords** (15 points each)
   - Core domain terms (e.g., "ansible", "systemctl", "update")

2. **Command Patterns** (10-12 points each)
   - Linux commands, package managers, file extensions

3. **Context Patterns** (20 points)
   - Regex matches for code blocks, API calls, specific syntax

4. **Conversation History** (10 points)
   - Continuity with previous expert selections

5. **Current Expert Bias** (5 points)
   - Slight preference to continue with same expert

## Usage Examples

### Linux Administration
```
User: "How do I check disk space with df command?"
→ Routes to: 🐧 Linux System Admin
→ Confidence: 85%
→ Keywords: df, disk, command
```

### Ansible Automation
```
User: "Write a playbook to install nginx with handlers"
→ Routes to: ⚙️ Ansible Automation Expert
→ Confidence: 92%
→ Keywords: playbook, install, handlers
```

### Update Management
```
User: "Schedule security patches for my fleet next week"
→ Routes to: 📦 Package Update Manager
→ Confidence: 88%
→ Keywords: schedule, security, patches, fleet
```

### FleetPulse Operations
```
User: "Get the status of all hosts in FleetPulse"
→ Routes to: 🚀 FleetPulse Operations
→ Confidence: 95%
→ Keywords: status, hosts, FleetPulse
```

## UI Components

### Smart Expert Panel
The main interface now shows:
- **Auto-Selected Expert**: Current expert with confidence indicator
- **Routing Reasoning**: Why this expert was chosen
- **Override Option**: Manual expert selection if needed
- **Alternative Suggestions**: For low-confidence selections

### Expert Routing Insights
Toggle detailed analysis showing:
- Matched keywords and patterns
- Context factors considered
- Routing decision process
- Performance tips for better routing

## Configuration

### Sidebar Settings
```
🧠 Expert Routing Settings
├── Show Expert Routing Analysis
├── Reset Expert Selection
└── Manual Override Options
```

### Confidence Thresholds
- **High Confidence**: > 70% (Green indicator)
- **Medium Confidence**: 40-70% (Orange indicator) 
- **Low Confidence**: < 40% (Red indicator, shows alternatives)

## API Integration

### Expert Router Class
```python
from core.expert_router import ExpertRouter, ExpertType

router = ExpertRouter()
result = router.route_query(
    user_query="How do I check system logs?",
    conversation_history=previous_messages,
    current_expert="general"
)

print(f"Expert: {result.expert_type.value}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Reasoning: {result.reasoning}")
```

### Routing Result
```python
@dataclass
class ExpertMatch:
    expert_type: ExpertType
    confidence: float
    reasoning: str
    keywords_matched: List[str]
    context_factors: List[str]
```

## Advanced Features

### Context-Aware Routing
The system maintains conversation context:
```
1. User: "How do I write an Ansible playbook?"
   → Ansible Expert

2. User: "Now add error handling"
   → Still Ansible Expert (context continuity)
```

### Alternative Suggestions
For ambiguous queries, the system suggests alternatives:
```
Query: "How do I monitor performance?"
Primary: Linux System Admin (45%)
Alternatives:
- FleetPulse Operations (40%) - for fleet monitoring
- Package Update Manager (25%) - for update performance
```

### Pattern-Based Detection
Recognizes specific patterns:
- Command syntax: `sudo systemctl restart nginx`
- API calls: `GET /hosts`
- File types: `playbook.yml`
- FleetPulse terms: `localhost:8000/health`

## Benefits

### For Users
- **Seamless Experience**: No manual expert selection required
- **Smart Suggestions**: System learns from context
- **Transparency**: Clear reasoning for routing decisions
- **Flexibility**: Override options when needed

### For Developers
- **Extensible**: Easy to add new experts and keywords
- **Configurable**: Adjustable confidence thresholds
- **Observable**: Built-in analytics and insights
- **Testable**: Comprehensive test suite included

## Testing

Run the expert routing tests:
```bash
python examples/test_expert_routing.py
```

Expected output:
```
🎯 Expert Routing Test Results
✅ Query: "How do I check disk space on my servers?"
   Expected: linux_admin
   Got: linux_admin (confidence: 85%)
   
🎯 Accuracy: 18/20 (90%)
✅ Routing accuracy looks good!
```

## Performance Considerations

- **Lightweight**: Keyword matching is O(n) where n = query length
- **Cached**: Expert descriptions and patterns are pre-computed
- **Efficient**: No external API calls for basic routing
- **Scalable**: Can handle concurrent routing requests

## Future Enhancements

### Planned Features
- **Machine Learning**: Train on user feedback for better routing
- **Custom Experts**: User-defined expert domains
- **Multi-Expert**: Route to multiple experts for complex queries
- **Learning Mode**: Adapt keywords based on user corrections

### Integration Ideas
- **Voice Commands**: Route based on speech patterns
- **File Analysis**: Route based on uploaded file types
- **Calendar Integration**: Time-based expert routing
- **User Profiles**: Personalized routing preferences

## Troubleshooting

### Common Issues

**Low Routing Accuracy**
- Add domain-specific keywords to `expert_keywords`
- Adjust confidence thresholds
- Review and add context patterns

**Unexpected Expert Selection**
- Check for keyword overlap between experts
- Use expert override for specific cases
- Enable routing insights for debugging

**Performance Issues**
- Profile keyword matching performance
- Consider caching for repeated queries
- Optimize regex patterns

### Debug Mode
Enable detailed logging:
```python
import logging
logging.getLogger('core.expert_router').setLevel(logging.DEBUG)
```

## Contributing

To extend the routing system:

1. **Add Keywords**: Update `_initialize_expert_keywords()`
2. **Add Patterns**: Update `_initialize_context_patterns()`
3. **Add Experts**: Extend `ExpertType` enum
4. **Test Changes**: Run test suite and validate accuracy

See `examples/test_expert_routing.py` for testing patterns.
