"""
Intelligent expert routing system for FleetPulse chatbot.

Automatically determines the most appropriate expert based on user queries
using keyword analysis, semantic understanding, and context awareness.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExpertType(Enum):
    """Available expert types for automatic routing."""
    GENERAL = "general"
    LINUX_ADMIN = "linux_admin"
    ANSIBLE = "ansible"
    UPDATES = "updates"
    FLEETPULSE = "fleetpulse"


@dataclass
class ExpertMatch:
    """Result of expert routing analysis."""
    expert_type: ExpertType
    confidence: float
    reasoning: str
    keywords_matched: List[str]
    context_factors: List[str]


class ExpertRouter:
    """
    Intelligent routing system that automatically selects the most appropriate
    expert based on user queries and conversation context.
    """
    
    def __init__(self):
        self.expert_keywords = self._initialize_expert_keywords()
        self.context_patterns = self._initialize_context_patterns()
        self.expert_descriptions = {
            ExpertType.GENERAL: "🤖 General Assistant",
            ExpertType.LINUX_ADMIN: "🐧 Linux System Admin",
            ExpertType.ANSIBLE: "⚙️ Ansible Automation Expert",
            ExpertType.UPDATES: "📦 Package Update Manager",
            ExpertType.FLEETPULSE: "🚀 FleetPulse Operations"
        }
    
    def _initialize_expert_keywords(self) -> Dict[ExpertType, Dict[str, List[str]]]:
        """Initialize keyword mappings for each expert type."""
        return {
            ExpertType.LINUX_ADMIN: {
                "primary": [
                    "linux", "ubuntu", "debian", "centos", "rhel", "fedora", "suse",
                    "systemd", "systemctl", "service", "daemon", "process",
                    "kernel", "module", "driver", "hardware",
                    "filesystem", "mount", "disk", "partition", "lvm", "raid",
                    "network", "interface", "iptables", "firewall", "ssh",
                    "user", "group", "permission", "chmod", "chown", "sudo",
                    "log", "syslog", "journalctl", "dmesg", "var/log",
                    "cpu", "memory", "ram", "performance", "monitoring",
                    "security", "selinux", "apparmor", "fail2ban"
                ],
                "commands": [
                    "ps", "top", "htop", "kill", "killall", "nohup",
                    "ls", "cd", "pwd", "find", "grep", "awk", "sed",
                    "cat", "tail", "head", "less", "more", "vi", "nano",
                    "df", "du", "free", "uptime", "who", "w", "last",
                    "netstat", "ss", "iftop", "tcpdump", "ping", "traceroute",
                    "crontab", "at", "jobs", "bg", "fg", "screen", "tmux"
                ],
                "package_managers": [
                    "apt", "apt-get", "dpkg", "yum", "dnf", "rpm", "zypper",
                    "pacman", "emerge", "portage", "snap", "flatpak", "appimage"
                ]
            },
            
            ExpertType.ANSIBLE: {
                "primary": [
                    "ansible", "playbook", "playbooks", "role", "roles",
                    "inventory", "host", "group", "vars", "variable",
                    "task", "tasks", "handler", "handlers", "template",
                    "jinja2", "jinja", "when", "loop", "with_items",
                    "vault", "encrypted", "secret", "password",
                    "galaxy", "collection", "module", "plugin",
                    "idempotent", "idempotency", "check mode", "dry run"
                ],
                "keywords": [
                    "automation", "orchestration", "configuration management",
                    "infrastructure as code", "iac", "devops", "ci/cd",
                    "deploy", "deployment", "provision", "provisioning",
                    "remote", "ssh", "winrm", "connection", "become", "sudo"
                ],
                "file_types": [
                    "yml", "yaml", "j2", "ansible.cfg", "hosts", "site.yml",
                    "main.yml", "vars.yml", "defaults.yml", "meta.yml"
                ]
            },
            
            ExpertType.UPDATES: {
                "primary": [
                    "update", "updates", "upgrade", "upgrades", "patch", "patches",
                    "package", "packages", "version", "versions", "dependency",
                    "security", "vulnerability", "cve", "critical", "urgent",
                    "rollback", "downgrade", "revert", "restore", "backup",
                    "schedule", "scheduled", "maintenance", "window", "downtime"
                ],
                "fleet_operations": [
                    "fleet", "mass", "bulk", "batch", "multiple", "all hosts",
                    "canary", "staged", "phased", "rolling", "deployment",
                    "coordination", "orchestrate", "synchronize", "sequence",
                    "risk", "assessment", "impact", "analysis", "testing",
                    "approval", "workflow", "change management", "compliance"
                ],
                "monitoring": [
                    "status", "progress", "report", "dashboard", "metrics",
                    "success", "failure", "error", "timeout", "retry",
                    "notification", "alert", "warning", "health check"
                ]
            },
            
            ExpertType.FLEETPULSE: {
                "primary": [
                    "fleetpulse", "fleet pulse", "api", "backend", "frontend",
                    "database", "sqlite", "docker", "container", "compose",
                    "fastapi", "react", "endpoint", "route", "health",
                    "opentelemetry", "jaeger", "tracing", "observability",
                    "mcp", "model context protocol", "tool", "tools"
                ],                "data_operations": [
                    "host", "hosts", "report", "reports", "history",
                    "status", "metrics", "data", "query", "database",
                    "export", "import", "backup", "restore", "migration",
                    "fleet report", "generate report", "fleet status"
                ],
                "api_endpoints": [
                    "/report", "/hosts", "/history", "/health", "/metrics",
                    "get_fleet_status", "get_host_details", "get_update_history",
                    "get_pending_updates", "get_system_metrics", "generate_fleet_report"
                ],
                "troubleshooting": [
                    "error", "problem", "issue", "debug", "troubleshoot",
                    "log", "logs", "service", "restart", "down", "unavailable",
                    "connection", "timeout", "failed", "broken", "fix"
                ]
            }
        }
    
    def _initialize_context_patterns(self) -> Dict[str, ExpertType]:
        """Initialize regex patterns for context-based routing."""
        return {
            # Command-like patterns
            r'\b(sudo|systemctl|service|ps|top|df|free|mount)\s+\w+': ExpertType.LINUX_ADMIN,
            r'\bapt(-get)?\s+(install|update|upgrade|remove)\b': ExpertType.LINUX_ADMIN,
            r'\byum\s+(install|update|remove|search)\b': ExpertType.LINUX_ADMIN,
            
            # Ansible-specific patterns
            r'\bansible(-playbook|-galaxy|-vault)?\s+': ExpertType.ANSIBLE,
            r'---\s*\n.*tasks:\s*\n': ExpertType.ANSIBLE,
            r'\b(when|loop|with_items|become|hosts):\s*': ExpertType.ANSIBLE,
              # FleetPulse API patterns
            r'(GET|POST|PUT|DELETE)\s+/(hosts?|report|history|health)': ExpertType.FLEETPULSE,
            r'\b(localhost:8000|fleetpulse.*(api|backend))\b': ExpertType.FLEETPULSE,
            r'\b(generate|create).*fleet.*report\b': ExpertType.FLEETPULSE,
            r'\bfleet.*(status|report|health|overview)\b': ExpertType.FLEETPULSE,
            
            # Update management patterns
            r'\b(pending|available|security)\s+updates?\b': ExpertType.UPDATES,
            r'\b(rollback|roll\s*back|revert)\s+(update|upgrade|patch)': ExpertType.UPDATES,
            r'\b(fleet|mass|bulk)\s+(update|upgrade|patch)': ExpertType.UPDATES,
        }
    
    def route_query(
        self, 
        user_query: str, 
        conversation_history: Optional[List[Dict]] = None,
        current_expert: Optional[str] = None
    ) -> ExpertMatch:
        """
        Analyze user query and determine the most appropriate expert.
        
        Args:
            user_query: The user's question or request
            conversation_history: Previous conversation context
            current_expert: Currently selected expert (for context)
            
        Returns:
            ExpertMatch with routing decision and reasoning
        """
        query_lower = user_query.lower()
        
        # Score each expert type
        expert_scores = {}
        matched_keywords = {}
        context_factors = []
        
        for expert_type in ExpertType:
            score, keywords = self._score_expert_match(query_lower, expert_type)
            expert_scores[expert_type] = score
            matched_keywords[expert_type] = keywords
        
        # Apply context patterns
        pattern_expert = self._check_context_patterns(user_query)
        if pattern_expert:
            expert_scores[pattern_expert] += 20
            context_factors.append(f"Context pattern matched for {pattern_expert.value}")
        
        # Consider conversation history
        if conversation_history:
            history_expert = self._analyze_conversation_context(conversation_history)
            if history_expert:
                expert_scores[history_expert] += 10
                context_factors.append(f"Conversation context suggests {history_expert.value}")
        
        # Apply current expert bias (slight preference to continue with same expert)
        if current_expert and current_expert != "general":
            try:
                current_expert_type = ExpertType(current_expert)
                expert_scores[current_expert_type] += 5
                context_factors.append(f"Continuity with current expert {current_expert}")
            except ValueError:
                pass
          # Determine best match
        best_expert = max(expert_scores.keys(), key=lambda x: expert_scores[x])
        best_score = expert_scores[best_expert]
        
        # Calculate confidence (normalize score to 0-1 range)
        max_possible_score = 100  # Theoretical maximum
        confidence = min(best_score / max_possible_score, 1.0)
        
        # If no clear winner, default to general
        if best_score < 15:  # Minimum threshold for expert routing
            best_expert = ExpertType.GENERAL
            confidence = 0.3
            reasoning = "No specific expertise domain detected, using general assistant"
        else:
            reasoning = self._generate_reasoning(
                best_expert, 
                matched_keywords[best_expert], 
                context_factors
            )
        
        return ExpertMatch(
            expert_type=best_expert,
            confidence=confidence,
            reasoning=reasoning,
            keywords_matched=matched_keywords[best_expert],
            context_factors=context_factors
        )
    
    def _score_expert_match(self, query: str, expert_type: ExpertType) -> Tuple[float, List[str]]:
        """Score how well a query matches an expert type."""
        if expert_type == ExpertType.GENERAL:
            return 5, []  # Base score for general
        
        keywords = self.expert_keywords.get(expert_type, {})
        score = 0
        matched = []
        
        # Score each keyword category with different weights
        for category, keyword_list in keywords.items():
            category_weight = {
                "primary": 15,
                "commands": 10,
                "package_managers": 12,
                "keywords": 8,
                "file_types": 10,
                "fleet_operations": 12,
                "monitoring": 8,
                "data_operations": 10,
                "api_endpoints": 15,
                "troubleshooting": 8            }.get(category, 5)
            
            for keyword in keyword_list:
                # Skip very short keywords that might cause false positives
                if len(keyword) < 2:
                    continue
                    
                if keyword in query:
                    score += category_weight
                    matched.append(keyword)
                    
                    # Bonus for exact matches or word boundaries
                    if re.search(rf'\b{re.escape(keyword)}\b', query):
                        score += 3
        
        return score, matched
    
    def _check_context_patterns(self, query: str) -> Optional[ExpertType]:
        """Check if query matches specific context patterns."""
        for pattern, expert_type in self.context_patterns.items():
            if re.search(pattern, query, re.IGNORECASE | re.MULTILINE):
                return expert_type
        return None
    
    def _analyze_conversation_context(self, history: List[Dict]) -> Optional[ExpertType]:
        """Analyze conversation history for expert context."""
        if not history:
            return None
        
        # Look at recent messages for context
        recent_messages = history[-3:] if len(history) > 3 else history
        combined_text = " ".join([msg.get("content", "") for msg in recent_messages])
        
        # Quick scoring of recent context
        expert_scores = {}
        for expert_type in ExpertType:
            if expert_type == ExpertType.GENERAL:
                continue
            score, _ = self._score_expert_match(combined_text.lower(), expert_type)
            expert_scores[expert_type] = score
        
        # Return expert with highest score if above threshold
        if expert_scores:
            best_expert = max(expert_scores.keys(), key=lambda x: expert_scores[x])
            if expert_scores[best_expert] > 10:
                return best_expert
        
        return None
    
    def _generate_reasoning(
        self, 
        expert_type: ExpertType, 
        keywords: List[str], 
        context_factors: List[str]
    ) -> str:
        """Generate human-readable reasoning for expert selection."""
        reasons = []
        
        if keywords:
            keyword_sample = keywords[:3]  # Show first 3 keywords
            reasons.append(f"Keywords detected: {', '.join(keyword_sample)}")
            if len(keywords) > 3:
                reasons.append(f"and {len(keywords) - 3} more related terms")
        
        if context_factors:
            reasons.extend(context_factors)
        
        expert_name = self.expert_descriptions[expert_type]
        base_reason = f"Routing to {expert_name}"
        
        if reasons:
            return f"{base_reason} based on: {'; '.join(reasons)}"
        else:
            return f"{base_reason} (default selection)"
    
    def get_expert_description(self, expert_type: ExpertType) -> str:
        """Get human-readable description of expert type."""
        return self.expert_descriptions.get(expert_type, "Unknown Expert")
    
    def suggest_alternatives(self, query: str, current_match: ExpertMatch) -> List[ExpertMatch]:
        """Suggest alternative experts if the primary match has low confidence."""
        if current_match.confidence > 0.7:
            return []  # High confidence, no alternatives needed
        
        alternatives = []
        query_lower = query.lower()
        
        # Find other potential matches
        for expert_type in ExpertType:
            if expert_type == current_match.expert_type:
                continue
            
            score, keywords = self._score_expert_match(query_lower, expert_type)
            if score > 10:  # Only suggest if reasonable match
                confidence = min(score / 100, 1.0)
                reasoning = f"Alternative based on: {', '.join(keywords[:2])}"
                
                alternatives.append(ExpertMatch(
                    expert_type=expert_type,
                    confidence=confidence,
                    reasoning=reasoning,
                    keywords_matched=keywords,
                    context_factors=[]
                ))
        
        # Sort by confidence and return top 2
        alternatives.sort(key=lambda x: x.confidence, reverse=True)
        return alternatives[:2]
