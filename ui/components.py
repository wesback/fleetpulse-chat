"""Custom Streamlit components for FleetPulse chatbot."""

import streamlit as st
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.genai_manager import ChatMessage
from core.mcp_client import MCPTool, MCPToolResult
from config.prompts import get_prompt_descriptions


def render_provider_selector(available_providers: List[str], current_provider: str) -> str:
    """Render AI provider selection dropdown."""
    provider_options = {
        "openai": "🤖 OpenAI GPT-4",
        "anthropic": "🧠 Anthropic Claude",
        "google": "🔍 Google Gemini",
        "azure": "☁️ Azure OpenAI",
        "ollama": "🏠 Ollama (Local)"
    }
    
    # Filter to only show available providers
    available_options = {
        k: v for k, v in provider_options.items() 
        if k in available_providers
    }
    
    if not available_options:
        st.error("No AI providers configured. Please check your environment variables.")
        return current_provider
    
    selected = st.selectbox(
        "AI Provider",
        options=list(available_options.keys()),
        format_func=lambda x: available_options[x],
        index=list(available_options.keys()).index(current_provider) if current_provider in available_options else 0,
        key="provider_selector"
    )
    
    return selected


def render_prompt_selector(current_prompt: str = "general") -> str:
    """Render system prompt selection dropdown."""
    prompt_descriptions = get_prompt_descriptions()
    
    prompt_options = {
        "general": "🤖 General Assistant",
        "linux_admin": "🐧 Linux System Admin",
        "ansible": "⚙️ Ansible Automation Expert",
        "updates": "📦 Package Update Manager",
        "fleetpulse": "🚀 FleetPulse Operations"
    }
    
    selected = st.selectbox(
        "Expert Mode",
        options=list(prompt_options.keys()),
        format_func=lambda x: prompt_options[x],
        index=list(prompt_options.keys()).index(current_prompt) if current_prompt in prompt_options else 0,
        key="prompt_selector"
    )
    
    # Show description
    with st.expander("ℹ️ Expert Mode Description", expanded=False):
        st.write(prompt_descriptions.get(selected, "General purpose assistant"))
    
    return selected


def render_chat_message(message: ChatMessage, show_timestamp: bool = True):
    """Render a chat message with appropriate styling."""
    with st.chat_message(message.role):
        st.write(message.content)
        
        if show_timestamp and message.timestamp:
            st.caption(f"*{message.timestamp}*")


def render_mcp_tool_result(tool_name: str, result: MCPToolResult, expanded: bool = False):
    """Render MCP tool execution result."""
    if result.success:
        status_icon = "✅"
        status_color = "green"
    else:
        status_icon = "❌"
        status_color = "red"
    
    with st.expander(f"{status_icon} Tool: {tool_name}", expanded=expanded):
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.write(f"**Status:** :{status_color}[{'Success' if result.success else 'Failed'}]")
        
        with col2:
            if result.success and result.data:
                if isinstance(result.data, dict):
                    st.json(result.data)
                elif isinstance(result.data, list):
                    for i, item in enumerate(result.data):
                        st.write(f"**Item {i+1}:**")
                        if isinstance(item, dict):
                            st.json(item)
                        else:
                            st.write(item)
                else:
                    st.write(result.data)
            elif result.error:
                st.error(f"Error: {result.error}")


def render_fleet_status_card(fleet_data: Dict[str, Any]):
    """Render fleet status overview card."""
    st.subheader("🚀 Fleet Status Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_hosts = fleet_data.get("total_hosts", 0)
        st.metric("Total Hosts", total_hosts)
    
    with col2:
        healthy_hosts = fleet_data.get("healthy_hosts", 0)
        st.metric("Healthy", healthy_hosts, delta=None)
    
    with col3:
        pending_updates = fleet_data.get("pending_updates", 0)
        st.metric("Pending Updates", pending_updates, delta=None)
    
    with col4:
        critical_issues = fleet_data.get("critical_issues", 0)
        delta_color = "inverse" if critical_issues > 0 else "normal"
        st.metric("Critical Issues", critical_issues, delta=None, delta_color=delta_color)
    
    # Health percentage
    if total_hosts > 0:
        health_percentage = (healthy_hosts / total_hosts) * 100
        st.progress(health_percentage / 100)
        st.caption(f"Fleet Health: {health_percentage:.1f}%")


def render_host_details_card(host_data: Dict[str, Any]):
    """Render detailed host information card."""
    st.subheader(f"🖥️ Host: {host_data.get('hostname', 'Unknown')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**System Information**")
        st.write(f"OS: {host_data.get('os', 'Unknown')}")
        st.write(f"Kernel: {host_data.get('kernel', 'Unknown')}")
        st.write(f"Uptime: {host_data.get('uptime', 'Unknown')}")
        st.write(f"Last Seen: {host_data.get('last_seen', 'Unknown')}")
    
    with col2:
        st.write("**Package Information**")
        st.write(f"Installed: {host_data.get('packages_installed', 0)}")
        st.write(f"Available Updates: {host_data.get('updates_available', 0)}")
        st.write(f"Security Updates: {host_data.get('security_updates', 0)}")
        
        if host_data.get('updates_available', 0) > 0:
            st.warning("Updates available")
        else:
            st.success("System up to date")


def render_package_list(packages: List[Dict[str, Any]], title: str = "Packages"):
    """Render a list of packages with details."""
    st.subheader(f"📦 {title}")
    
    if not packages:
        st.info("No packages to display")
        return
    
    for pkg in packages:
        with st.expander(f"{pkg.get('name', 'Unknown')} - {pkg.get('version', 'Unknown')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Current Version:** {pkg.get('current_version', 'Unknown')}")
                st.write(f"**Available Version:** {pkg.get('available_version', 'Unknown')}")
            
            with col2:
                severity = pkg.get('severity', 'Unknown')
                if severity.lower() in ['critical', 'high']:
                    st.error(f"Severity: {severity}")
                elif severity.lower() == 'medium':
                    st.warning(f"Severity: {severity}")
                else:
                    st.info(f"Severity: {severity}")
                
                st.write(f"**Description:** {pkg.get('description', 'No description available')}")


def render_update_history(history: List[Dict[str, Any]]):
    """Render update history timeline."""
    st.subheader("📜 Update History")
    
    if not history:
        st.info("No update history available")
        return
    
    for update in history:
        date = update.get('date', 'Unknown')
        packages = update.get('packages', [])
        
        with st.expander(f"📅 {date} - {len(packages)} packages updated"):
            if packages:
                for pkg in packages:
                    st.write(f"• **{pkg.get('name')}**: {pkg.get('old_version')} → {pkg.get('new_version')}")
            else:
                st.write("No package details available")


def render_configuration_panel():
    """Render configuration and settings panel."""
    st.sidebar.subheader("⚙️ Configuration")
    
    # Model parameters
    with st.sidebar.expander("Model Parameters", expanded=False):
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 100, 4000, 2000, 100)
        
        return {
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    return {"temperature": 0.7, "max_tokens": 2000}


def render_conversation_sidebar(conversations: List[Dict[str, Any]], current_conversation_id: Optional[int] = None):
    """Render conversation history sidebar."""
    st.sidebar.subheader("💬 Conversations")
    
    # New conversation button
    if st.sidebar.button("➕ New Conversation", use_container_width=True):
        return "new"
    
    # Search conversations
    search_query = st.sidebar.text_input("🔍 Search conversations", placeholder="Search...")
    
    # List conversations
    selected_conversation = current_conversation_id
    
    for conv in conversations:
        conv_id = conv.get('id')
        title = conv.get('title', 'Untitled')
        updated_at = conv.get('updated_at', '')
        
        # Truncate long titles
        display_title = title[:30] + "..." if len(title) > 30 else title
        
        # Highlight current conversation
        is_current = conv_id == current_conversation_id
        
        if st.sidebar.button(
            f"{'📌 ' if is_current else '💬 '}{display_title}",
            key=f"conv_{conv_id}",
            use_container_width=True,
            type="primary" if is_current else "secondary"
        ):
            selected_conversation = conv_id
    
    return selected_conversation


def render_tool_usage_display(tools_used: List[Dict[str, Any]]):
    """Display tools that were used in the conversation."""
    if not tools_used:
        return
    
    st.sidebar.subheader("🔧 Tools Used")
    
    for tool in tools_used:
        tool_name = tool.get('name', 'Unknown')
        success = tool.get('success', False)
        icon = "✅" if success else "❌"
        
        with st.sidebar.expander(f"{icon} {tool_name}", expanded=False):
            if tool.get('parameters'):
                st.write("**Parameters:**")
                st.json(tool['parameters'])
            
            if success and tool.get('result'):
                st.write("**Result:**")
                st.success("Executed successfully")
            elif tool.get('error'):
                st.write("**Error:**")
                st.error(tool['error'])


def render_status_indicators(genai_status: bool, mcp_status: bool, fleetpulse_status: bool):
    """Render status indicators for system components."""
    st.sidebar.subheader("🚦 System Status")
    
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if genai_status:
            st.success("AI")
        else:
            st.error("AI")
    
    with col2:
        if mcp_status:
            st.success("MCP")
        else:
            st.error("MCP")
    
    with col3:
        if fleetpulse_status:
            st.success("Fleet")
        else:
            st.error("Fleet")


def render_error_message(error: str, suggestion: Optional[str] = None):
    """Render formatted error message with optional suggestion."""
    st.error(f"❌ **Error:** {error}")
    
    if suggestion:
        st.info(f"💡 **Suggestion:** {suggestion}")


def render_loading_spinner(message: str = "Processing..."):
    """Render loading spinner with message."""
    with st.spinner(message):
        return st.empty()


def render_welcome_screen():
    """Render welcome screen for new users."""
    st.title("🚀 FleetPulse GenAI Chatbot")
    
    st.markdown("""
    Welcome to the FleetPulse GenAI Chatbot! This intelligent assistant helps you manage your Linux fleet 
    with the power of multiple AI providers and Model Context Protocol (MCP) integration.
    
    ## 🎯 What can I help you with?
    
    ### 🐧 Linux System Administration
    - Package management across distributions
    - System monitoring and troubleshooting
    - Security best practices
    - Performance optimization
    
    ### ⚙️ Ansible Automation
    - Playbook development and optimization
    - Inventory management
    - Role creation and best practices
    - Troubleshooting automation workflows
    
    ### 📦 Package Update Management
    - Fleet-wide update coordination
    - Risk assessment and planning
    - Rollback strategies
    - Compliance and security patches
    
    ### 🚀 FleetPulse Operations
    - Query fleet status and metrics
    - Generate comprehensive reports
    - Schedule update operations
    - Monitor system health
    
    ## 🔧 Available Tools
    
    I have access to FleetPulse tools that let me:
    - Check fleet status and host details
    - Retrieve update history and pending updates
    - Generate reports and schedule operations
    - Monitor system metrics and performance
    
    ## 🚀 Getting Started
    
    1. **Select an AI Provider** from the dropdown above
    2. **Choose an Expert Mode** that matches your needs
    3. **Start chatting** - ask me anything about your fleet!
    
    **Example questions to try:**
    - "What's the current status of my fleet?"
    - "Show me hosts with pending security updates"
    - "Help me create an Ansible playbook for package updates"
    - "What are the best practices for rolling out kernel updates?"
    """)
    
    # Quick action buttons
    st.subheader("🎯 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Check Fleet Status", use_container_width=True):
            return "check_fleet_status"
    
    with col2:
        if st.button("📦 Pending Updates", use_container_width=True):
            return "check_pending_updates"
    
    with col3:
        if st.button("📈 Generate Report", use_container_width=True):
            return "generate_report"
    
    return None