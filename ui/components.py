"""Custom Streamlit components for FleetPulse chatbot."""

import streamlit as st
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from core.genai_manager import ChatMessage
from core.mcp_client import MCPTool, MCPToolResult, ErrorType
from core.expert_router import ExpertRouter, ExpertMatch, ExpertType
from config.prompts import get_prompt_descriptions
from utils.mcp_diagnostics import MCPDiagnosticRunner, DiagnosticResult, generate_diagnostic_report


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


def render_auto_expert_selector(
    user_query: str = "", 
    conversation_history: Optional[List[Dict]] = None,
    current_expert: str = "general",
    show_reasoning: bool = True
) -> tuple[str, ExpertMatch]:
    """
    Render intelligent expert selector that auto-routes based on user query.
    
    Returns:
        tuple: (selected_expert, expert_match_info)
    """
    router = ExpertRouter()
    
    # Auto-route if we have a query
    if user_query.strip():
        expert_match = router.route_query(
            user_query, 
            conversation_history, 
            current_expert
        )
        auto_selected = expert_match.expert_type.value
    else:
        # No query yet, use current expert
        expert_match = ExpertMatch(
            expert_type=ExpertType(current_expert) if current_expert in [e.value for e in ExpertType] else ExpertType.GENERAL,
            confidence=1.0,
            reasoning="Current selection",
            keywords_matched=[],
            context_factors=[]
        )
        auto_selected = current_expert
    
    # Create columns for the expert display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show auto-selected expert with confidence indicator
        confidence_color = "green" if expert_match.confidence > 0.7 else "orange" if expert_match.confidence > 0.4 else "red"
        confidence_pct = int(expert_match.confidence * 100)
        
        expert_description = router.get_expert_description(expert_match.expert_type)
        
        st.info(f"🎯 **Auto-Selected Expert:** {expert_description}  \n"
               f"**Confidence:** :{confidence_color}[{confidence_pct}%]")
        
        if show_reasoning and expert_match.reasoning:
            st.caption(f"💭 {expert_match.reasoning}")
    
    with col2:
        # Override option
        if st.button("🔄 Change Expert", help="Override automatic expert selection"):
            st.session_state.show_expert_override = True
    
    # Show expert override options if requested
    selected_expert = auto_selected
    if st.session_state.get("show_expert_override", False):
        with st.expander("🛠️ Expert Override Options", expanded=True):
            prompt_options = {
                "general": "🤖 General Assistant",
                "linux_admin": "🐧 Linux System Admin", 
                "ansible": "⚙️ Ansible Automation Expert",
                "updates": "📦 Package Update Manager",
                "fleetpulse": "🚀 FleetPulse Operations"
            }
            
            selected_expert = st.selectbox(
                "Choose Expert:",
                options=list(prompt_options.keys()),
                format_func=lambda x: prompt_options[x],
                index=list(prompt_options.keys()).index(auto_selected) if auto_selected in prompt_options else 0,
                key="manual_expert_override"
            )
            
            col_apply, col_cancel = st.columns(2)
            with col_apply:
                if st.button("✅ Apply Override"):
                    st.session_state.show_expert_override = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel"):
                    st.session_state.show_expert_override = False
                    selected_expert = auto_selected
                    st.rerun()
        
        # Show alternative suggestions if confidence is low
        if expert_match.confidence < 0.6:
            alternatives = router.suggest_alternatives(user_query, expert_match)
            if alternatives:
                st.warning("🤔 **Low confidence in expert selection. Consider these alternatives:**")
                for alt in alternatives:
                    alt_desc = router.get_expert_description(alt.expert_type)
                    alt_confidence = int(alt.confidence * 100)
                    if st.button(f"{alt_desc} ({alt_confidence}%)", key=f"alt_{alt.expert_type.value}"):
                        st.session_state.show_expert_override = False
                        selected_expert = alt.expert_type.value
                        st.rerun()
    
    return selected_expert, expert_match


def render_prompt_selector(current_prompt: str = "general") -> str:
    """
    Legacy manual prompt selector - kept for backward compatibility.
    Consider using render_auto_expert_selector instead.
    """
    prompt_descriptions = get_prompt_descriptions()
    
    prompt_options = {
        "general": "🤖 General Assistant",
        "linux_admin": "🐧 Linux System Admin",
        "ansible": "⚙️ Ansible Automation Expert",
        "updates": "📦 Package Update Manager",
        "fleetpulse": "🚀 FleetPulse Operations"
    }
    
    selected = st.selectbox(
        "Expert Mode (Manual)",
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


def render_error_display(error_result: MCPToolResult):
    """Render comprehensive error display with diagnostics and recovery actions."""
    st.error("🚨 MCP Tool Error")
    
    # Error summary
    with st.expander("Error Details", expanded=True):
        st.write(f"**Tool:** {error_result.diagnostics.get('tool_name', 'Unknown') if error_result.diagnostics else 'Unknown'}")
        st.write(f"**Error Type:** {error_result.error_type.value if error_result.error_type else 'Unknown'}")
        st.write(f"**Message:** {error_result.error}")
        
        if error_result.diagnostics:
            if "timestamp" in error_result.diagnostics:
                timestamp = datetime.fromtimestamp(error_result.diagnostics["timestamp"])
                st.write(f"**Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if "status_code" in error_result.diagnostics:
                st.write(f"**HTTP Status:** {error_result.diagnostics['status_code']}")
    
    # Recovery guidance
    if error_result.diagnostics and "recovery_actions" in error_result.diagnostics:
        with st.expander("🔧 Recovery Actions", expanded=True):
            st.write("**Recommended steps to resolve this issue:**")
            for i, action in enumerate(error_result.diagnostics["recovery_actions"], 1):
                st.write(f"{i}. {action}")
    
    # Guidance based on error type
    if error_result.diagnostics and "guidance" in error_result.diagnostics:
        with st.expander("💡 Additional Guidance"):
            st.info(error_result.diagnostics["guidance"])
    
    # Technical details (collapsible)
    if error_result.diagnostics:
        with st.expander("🔍 Technical Details", expanded=False):
            st.json(error_result.diagnostics)


def render_diagnostic_panel():
    """Render MCP diagnostic panel."""
    st.subheader("🏥 MCP System Diagnostics")
    
    if st.button("Run Full Diagnostics", type="primary"):
        with st.spinner("Running comprehensive diagnostics..."):
            try:
                # Run diagnostics asynchronously
                runner = MCPDiagnosticRunner()
                
                # Use asyncio.run to handle the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    results = loop.run_until_complete(runner.run_full_diagnostics())
                finally:
                    loop.close()
                
                # Display results
                render_diagnostic_results(results)
                
            except Exception as e:
                st.error(f"Diagnostic runner failed: {str(e)}")
                st.write("Please check the MCP service configuration and try again.")


def render_diagnostic_results(results: List[DiagnosticResult]):
    """Render diagnostic results in a structured format."""
    # Summary metrics
    healthy_count = sum(1 for r in results if r.status == "healthy")
    warning_count = sum(1 for r in results if r.status == "warning")
    error_count = sum(1 for r in results if r.status == "error")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Healthy", healthy_count, delta=None, delta_color="normal")
    with col2:
        st.metric("Warnings", warning_count, delta=None, delta_color="inverse")
    with col3:
        st.metric("Errors", error_count, delta=None, delta_color="inverse")
    
    # Detailed results
    st.subheader("Detailed Results")
    
    for result in results:
        # Status icon and color
        if result.status == "healthy":
            icon = "✅"
            status_color = "green"
        elif result.status == "warning":
            icon = "⚠️"
            status_color = "orange"
        else:
            icon = "❌"
            status_color = "red"
        
        # Create container for each result
        with st.container():
            st.markdown(f"**{icon} {result.name}**")
            st.markdown(f":{status_color}[{result.message}]")
            
            # Show recovery actions if available
            if result.recovery_actions:
                with st.expander(f"Recovery Actions for {result.name}"):
                    for i, action in enumerate(result.recovery_actions, 1):
                        st.write(f"{i}. {action}")
            
            # Show technical details if available
            if result.details:
                with st.expander(f"Technical Details for {result.name}"):
                    st.json(result.details)
            
            st.divider()
    
    # Generate downloadable report
    if st.button("📄 Generate Diagnostic Report"):
        report = generate_diagnostic_report(results)
        st.download_button(
            label="Download Report",
            data=report,
            file_name=f"fleetpulse_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


def render_tool_status_indicator(mcp_client):
    """Render real-time tool status indicator."""
    try:
        # Get diagnostics asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            diagnostics = loop.run_until_complete(mcp_client.get_diagnostics())
        finally:
            loop.close()
        
        # Display status indicator
        if diagnostics.backend_status == "healthy":
            st.success("🟢 MCP Tools: Online")
        elif diagnostics.backend_status == "unhealthy":
            st.error("🔴 MCP Tools: Offline")
        else:
            st.warning("🟡 MCP Tools: Unknown Status")
        
        # Show last successful call
        if diagnostics.last_successful_call:
            last_call = datetime.fromtimestamp(diagnostics.last_successful_call)
            st.caption(f"Last successful call: {last_call.strftime('%H:%M:%S')}")
        
        # Show error count
        if diagnostics.error_count > 0:
            st.caption(f"⚠️ {diagnostics.error_count} errors since startup")
            
    except Exception as e:
        st.warning(f"Unable to check tool status: {str(e)}")


def render_quick_recovery_panel(mcp_client):
    """Render quick recovery actions panel."""
    st.subheader("🔧 Quick Recovery")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset MCP Client"):
            try:
                # Reinitialize the client
                st.session_state.mcp_client = type(mcp_client)()
                st.success("MCP client reset successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reset client: {str(e)}")
    
    with col2:
        if st.button("🏥 Health Check"):
            with st.spinner("Performing health check..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        runner = MCPDiagnosticRunner()
                        backend_result = loop.run_until_complete(runner._check_backend_connectivity())
                        
                        if backend_result.status == "healthy":
                            st.success("✅ Backend is healthy")
                        else:
                            st.error(f"❌ Backend issue: {backend_result.message}")
                    finally:
                        loop.close()
                except Exception as e:
                    st.error(f"Health check failed: {str(e)}")


def render_tool_error_recovery_guide(error_type: ErrorType):
    """Render specific recovery guide based on error type."""
    st.subheader("🛠️ Error-Specific Recovery Guide")
    
    if error_type == ErrorType.NETWORK_ERROR:
        st.markdown("""
        **Network Connectivity Issue Detected**
        
        **Immediate Actions:**
        1. Check if FleetPulse backend is running
        2. Verify the backend URL configuration
        3. Test network connectivity manually
        
        **Commands to try:**
        ```bash
        # Test backend connectivity
        curl -f http://localhost:8000/health
        
        # Check if service is listening
        netstat -tulpn | grep :8000
        
        # Test TCP connection
        telnet localhost 8000
        ```
        """)
    
    elif error_type == ErrorType.DATABASE_ERROR:
        st.markdown("""
        **Database Access Issue Detected**
        
        **Immediate Actions:**
        1. Check database file permissions
        2. Verify database integrity
        3. Check for database locks
        
        **Commands to try:**
        ```bash
        # Check database integrity
        sqlite3 fleetpulse.db "PRAGMA integrity_check;"
        
        # Check file permissions
        ls -la fleetpulse.db
        
        # Check for locks
        fuser fleetpulse.db
        ```
        """)
    
    elif error_type == ErrorType.TIMEOUT_ERROR:
        st.markdown("""
        **Timeout Issue Detected**
        
        **Immediate Actions:**
        1. Check system resource usage
        2. Verify backend performance
        3. Consider increasing timeout values
        
        **Commands to try:**
        ```bash
        # Check system resources
        top
        free -h
        df -h
        
        # Check backend logs
        tail -f /var/log/fleetpulse.log
        ```
        """)
    
    elif error_type == ErrorType.AUTHENTICATION_ERROR:
        st.markdown("""
        **Authentication Issue Detected**
        
        **Immediate Actions:**
        1. Verify API keys and tokens
        2. Check service account permissions
        3. Refresh authentication if applicable
        
        **Configuration to check:**
        - Environment variables for API keys
        - Service account configuration
        - Token expiration times
        """)
    
    else:
        st.markdown("""
        **General Troubleshooting**
        
        **Immediate Actions:**
        1. Check application logs
        2. Verify service status
        3. Test individual components
        
        **Commands to try:**
        ```bash
        # Check service status
        systemctl status fleetpulse
        
        # Check logs
        journalctl -u fleetpulse -f
        
        # Test API endpoints
        curl -v http://localhost:8000/api/fleet/status
        ```
        """)


def render_expert_routing_insights(expert_match: ExpertMatch, show_details: bool = False):
    """
    Render detailed insights about expert routing decision.
    Useful for debugging and transparency.
    """
    if not show_details:
        return
    
    with st.expander("🧠 Expert Routing Analysis", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Analysis Results")
            st.write(f"**Selected Expert:** {expert_match.expert_type.value}")
            st.write(f"**Confidence:** {expert_match.confidence:.1%}")
            st.write(f"**Reasoning:** {expert_match.reasoning}")
            
            if expert_match.keywords_matched:
                st.write("**Keywords Matched:**")
                for keyword in expert_match.keywords_matched[:10]:  # Show first 10
                    st.markdown(f"- `{keyword}`")
                if len(expert_match.keywords_matched) > 10:
                    st.caption(f"... and {len(expert_match.keywords_matched) - 10} more")
        
        with col2:
            st.subheader("🔍 Context Factors")
            if expert_match.context_factors:
                for factor in expert_match.context_factors:
                    st.markdown(f"• {factor}")
            else:
                st.write("No additional context factors detected")
            
            # Show routing tips
            st.subheader("💡 Routing Tips")
            st.markdown("""
            **To improve routing accuracy:**
            - Use specific technical terms
            - Mention tools or commands
            - Include context about your goal
            - Reference systems or services
            """)


def render_smart_expert_panel(
    user_input: str = "",
    conversation_history: Optional[List[Dict]] = None,
    current_expert: str = "general",
    show_insights: bool = False
) -> str:
    """
    Render the complete smart expert selection panel with routing and insights.
    This is the main component to use for intelligent expert selection.
    """
    st.subheader("🎯 AI Expert Selection")
    
    # Initialize session state for expert override
    if "show_expert_override" not in st.session_state:
        st.session_state.show_expert_override = False
    
    # Get auto-selected expert and routing info
    selected_expert, expert_match = render_auto_expert_selector(
        user_input, 
        conversation_history, 
        current_expert,
        show_reasoning=True
    )
    
    # Show routing insights if requested
    if show_insights:
        render_expert_routing_insights(expert_match, show_details=True)
    
    return selected_expert