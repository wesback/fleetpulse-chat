"""
FleetPulse GenAI Chatbot - Main Streamlit Application

A comprehensive chatbot for FleetPulse fleet management with multi-provider AI support
and Model Context Protocol (MCP) integration.
"""

import streamlit as st
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

# Core imports
from config import GenAIProvider, get_settings, get_available_providers
from config.prompts import get_system_prompt
from core.genai_manager import GenAIManager, ChatMessage
from core.fastmcp_client import get_mcp_client
from core.conversation import ConversationManager

# UI imports
from ui.components import (
    render_provider_selector, render_prompt_selector, render_chat_message,
    render_configuration_panel, render_conversation_sidebar,
    render_welcome_screen, render_error_message, render_status_indicators,
    render_error_display, render_diagnostic_panel, render_tool_status_indicator,
    render_quick_recovery_panel, render_tool_error_recovery_guide,
    render_smart_expert_panel
)
from ui.dashboard import FleetDashboard, run_dashboard_async

# Utils imports
from utils.helpers import setup_logging, generate_conversation_title, format_timestamp
from utils.validators import sanitize_input, validate_mcp_tool_parameters, ValidationError
from utils.mcp_diagnostics import MCPDiagnosticRunner


# Configure Streamlit page
st.set_page_config(
    page_title="FleetPulse GenAI Chatbot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
logger = setup_logging()

# Initialize settings
settings = get_settings()


class FleetPulseChatbot:
    """Main chatbot application class."""
    
    def __init__(self):
        self.genai_manager = None
        self.mcp_client = None
        self.conversation_manager = ConversationManager()
        self.fleet_dashboard = FleetDashboard()
        self._async_init_started = False
    
    async def _async_initialize_components(self):
        """Async initialization for MCP and GenAI."""
        if not self._async_init_started:
            self._async_init_started = True
            try:
                self.genai_manager = GenAIManager()
                self.mcp_client = await get_mcp_client()
                logger.info("Async components initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize async components: %s", e)
                st.error(f"Initialization error: {e}")
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state."""
        if "current_conversation_id" not in st.session_state:
            st.session_state.current_conversation_id = None
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "ai_provider" not in st.session_state:
            available_providers = get_available_providers()
            st.session_state.ai_provider = available_providers[0].value if available_providers else "openai"
        
        if "system_prompt" not in st.session_state:
            st.session_state.system_prompt = "general"
        
        if "tools_used" not in st.session_state:            st.session_state.tools_used = []        
        if "model_params" not in st.session_state:
            st.session_state.model_params = {"temperature": 0.7, "max_tokens": 2000}
        
        if "show_dashboard" not in st.session_state:
            st.session_state.show_dashboard = False
        
        if "show_diagnostics" not in st.session_state:
            st.session_state.show_diagnostics = False
    
    def _check_system_status(self) -> Dict[str, bool]:
        """Check status of system components."""
        status = {
            "genai": bool(self.genai_manager and self.genai_manager.get_available_providers()),
            "mcp": bool(self.mcp_client),
            "fleetpulse": True  # Would check actual API connectivity
        }
        return status
    
    async def _run_system_diagnostics(self) -> List:
        """Run comprehensive system diagnostics."""
        try:
            runner = MCPDiagnosticRunner()
            return await runner.run_full_diagnostics()
        except Exception as e:
            logger.error(f"Diagnostic runner failed: {e}")
            return []
    
    def _handle_tool_error(self, tool_result):
        """Handle MCP tool errors with enhanced UI feedback."""
        if not tool_result.success:
            # Display comprehensive error information
            render_error_display(tool_result)
            
            # Show specific recovery guidance if error type is known
            if tool_result.error_type:
                render_tool_error_recovery_guide(tool_result.error_type)
            
            # Log error for debugging
            logger.error(f"Tool execution failed: {tool_result.error}")
            
            return False
        return True
    async def _detect_tool_usage(self, user_message: str) -> List[Dict[str, Any]]:
        """Detect if user message suggests tool usage."""
        tools_to_try = []
        message_lower = user_message.lower()
        
        # Enhanced keyword-based detection with natural language patterns
        tool_keywords = {
            "get_fleet_status": [
                "fleet status", "overall status", "fleet health", "fleet overview",
                "my hosts", "all hosts", "servers", "fleet summary", "how many hosts",
                "host status", "show me hosts", "list hosts", "hosts overview"
            ],
            "get_host_details": [
                "host details", "server info", "host info", "system details",
                "tell me about", "details about", "information about", "specific host",
                "particular server", "one host", "individual host"
            ],
            "get_pending_updates": [
                "pending updates", "available updates", "updates needed", "updates waiting",
                "need updates", "require updates", "outstanding updates", "updates available",
                "what updates", "which updates", "any updates"
            ],
            "get_update_history": [
                "update history", "update log", "previous updates", "past updates",
                "updates happened", "recent updates", "last updates", "update activity",
                "what happened", "what changed", "installation history", "package history",
                "last few days", "recently updated", "update timeline", "changes made"
            ],
            "generate_fleet_report": [
                "generate report", "fleet report", "create report", "full report",
                "comprehensive report", "summary report", "detailed report"
            ],
            "get_system_metrics": [
                "system metrics", "performance", "cpu usage", "memory usage",
                "resource usage", "system performance", "metrics", "monitoring",
                "system stats", "resource stats"
            ]
        }
        
        # Check for tool matches
        for tool_name, keywords in tool_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                tools_to_try.append({"name": tool_name, "keywords": keywords})
        
        # Special logic for complex queries        if any(word in message_lower for word in ["hosts", "servers", "fleet"]):
            if "update" in message_lower and any(time_ref in message_lower for time_ref in ["last", "recent", "past", "happened", "days", "week"]):
                # Query about recent updates across hosts
                if "get_update_history" not in [t["name"] for t in tools_to_try]:
                    tools_to_try.append({"name": "get_update_history", "keywords": ["updates happened"]})
                if "get_fleet_status" not in [t["name"] for t in tools_to_try]:
                    tools_to_try.append({"name": "get_fleet_status", "keywords": ["hosts"]})
        
        return tools_to_try
    
    async def _execute_suggested_tools(self, suggested_tools: List[Dict[str, Any]], user_message: str) -> List[Dict[str, Any]]:
        """Execute suggested tools and return results."""
        tool_results = []
        
        for tool_info in suggested_tools:
            tool_name = tool_info["name"]
            
            try:
                # Extract parameters from user message (simplified)
                parameters = self._extract_tool_parameters(tool_name, user_message)
                
                # Validate parameters
                validated_params = validate_mcp_tool_parameters(tool_name, parameters)
                
                # Execute tool with null check for mcp_client
                if not self.mcp_client:
                    logger.error("MCP client not initialized")
                    st.error("MCP client not available. Please check system status.")
                    continue
                
                result = await self.mcp_client.execute_tool(tool_name, validated_params)
                
                # Handle tool errors with enhanced error display
                if not result.success:
                    self._handle_tool_error(result)
                    
                    # Still record the failed attempt
                    tool_results.append({
                        "name": tool_name,
                        "parameters": validated_params,
                        "result": None,
                        "success": False,
                        "error": result.error
                    })
                else:
                    tool_results.append({
                        "name": tool_name,
                        "parameters": validated_params,
                        "result": result.data,
                        "success": True,
                        "error": None
                    })
                
                # Add to session state for display
                st.session_state.tools_used.append({
                    "name": tool_name,
                    "parameters": validated_params,
                    "success": result.success,
                    "error": result.error,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ValidationError as e:
                logger.warning("Parameter validation failed for %s: %s", tool_name, e)
                tool_results.append({
                    "name": tool_name,
                    "parameters": {},
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
            except Exception as e:
                logger.error("Tool execution failed for %s: %s", tool_name, e)
                tool_results.append({
                    "name": tool_name,
                    "parameters": {},
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
        
        return tool_results
    
    def _extract_tool_parameters(self, tool_name: str, message: str) -> Dict[str, Any]:
        """Extract parameters for tools from user message (enhanced)."""
        import re
        # datetime already imported at top
        
        params = {}
        message_lower = message.lower()
        
        # Extract hostnames (improved pattern)
        hostname_pattern = r'\b(?:host|server)\s+([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*)\b'
        hostname_matches = re.findall(hostname_pattern, message, re.IGNORECASE)
        hostnames = [match[0] for match in hostname_matches if match[0]]
        
        # Also look for standalone hostnames
        standalone_hostname_pattern = r'\b([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*)\b'
        standalone_matches = re.findall(standalone_hostname_pattern, message)
        standalone_hostnames = [match[0] for match in standalone_matches if match[0] and '.' in match[0]]
        
        all_hostnames = list(set(hostnames + standalone_hostnames))
        
        if tool_name in ["get_host_details", "get_update_history", "get_system_metrics"]:
            if all_hostnames:
                params["hostname"] = all_hostnames[0]
        
        if tool_name == "schedule_updates":
            if all_hostnames:
                params["hostnames"] = all_hostnames
        
        # Extract time periods for history queries
        if tool_name == "get_update_history":
            # Look for explicit day counts
            day_patterns = [
                r'(\d+)\s*days?',
                r'last\s+(\d+)\s*days?',
                r'past\s+(\d+)\s*days?',
                r'recent\s+(\d+)\s*days?'
            ]
            
            for pattern in day_patterns:
                day_match = re.search(pattern, message_lower)
                if day_match:
                    params["days"] = int(day_match.group(1))
                    break
            
            # Default time periods for common phrases
            if "days" not in params:
                if any(phrase in message_lower for phrase in ["last few days", "recent days", "past few days"]):
                    params["days"] = 7
                elif any(phrase in message_lower for phrase in ["last week", "past week", "this week"]):
                    params["days"] = 7
                elif any(phrase in message_lower for phrase in ["last month", "past month", "this month"]):
                    params["days"] = 30
                elif any(phrase in message_lower for phrase in ["yesterday", "last day"]):
                    params["days"] = 1
                elif any(phrase in message_lower for phrase in ["today", "recent", "latest"]):
                    params["days"] = 1
        
        # Extract severity levels
        if tool_name == "get_pending_updates":
            severity_patterns = [
                r'\b(critical|high|important|medium|moderate|low)\b',
                r'\b(urgent|emergency)\b',  # Map to critical
                r'\b(normal|regular)\b'     # Map to medium
            ]
            
            for pattern in severity_patterns:
                severity_match = re.search(pattern, message_lower)
                if severity_match:
                    severity = severity_match.group(1)
                    if severity in ["urgent", "emergency"]:
                        severity = "critical"
                    elif severity in ["normal", "regular"]:
                        severity = "medium"
                    params["severity"] = severity
                    break
        
        # Extract package names
        if tool_name == "check_package_info":
            package_patterns = [
                r'package\s+([a-zA-Z0-9\-_+\.]+)',
                r'([a-zA-Z0-9\-_+\.]+)\s+package',
                r'about\s+([a-zA-Z0-9\-_+\.]+)',
                r'info\s+([a-zA-Z0-9\-_+\.]+)'
            ]
            
            for pattern in package_patterns:
                package_match = re.search(pattern, message, re.IGNORECASE)
                if package_match:
                    params["package_name"] = package_match.group(1)
                    break
        
        return params
    
    async def _process_chat_message(self, user_message: str) -> str:
        """Process user message and return AI response."""
        try:
            # Sanitize input
            user_message = sanitize_input(user_message)
            
            # Get current conversation messages
            messages = []
            
            # Add system prompt
            system_prompt = get_system_prompt(st.session_state.system_prompt)
            messages.append(ChatMessage(role="system", content=system_prompt))
            
            # Add conversation history
            if st.session_state.current_conversation_id:
                history = self.conversation_manager.get_chat_history(st.session_state.current_conversation_id)
                messages.extend(history)
              # Add current user message
            messages.append(ChatMessage(role="user", content=user_message))
            
            # Check for tool usage - use both keyword detection and AI-driven selection
            suggested_tools = await self._detect_tool_usage(user_message)
            
            # If keyword detection didn't find tools, try AI-driven selection
            if not suggested_tools and self.genai_manager:
                ai_selected_tools = await self._ai_driven_tool_selection(user_message)
                suggested_tools.extend(ai_selected_tools)
            
            tool_context = ""
            
            if suggested_tools:
                tool_results = await self._execute_suggested_tools(suggested_tools, user_message)
                
                # Add tool results to context
                if tool_results:
                    tool_context = "\n\nTool Results:\n"
                    for result in tool_results:
                        if result["success"]:
                            tool_context += f"- {result['name']}: {result['result']}\n"
                        else:
                            tool_context += f"- {result['name']}: Error - {result['error']}\n"
            
            # Add tool context to message if available
            if tool_context:
                enhanced_message = user_message + tool_context
                messages[-1] = ChatMessage(role="user", content=enhanced_message)
            
            # Get AI response
            provider = GenAIProvider(st.session_state.ai_provider)
            response = await self.genai_manager.chat_completion(
                messages,
                provider=provider,
                **st.session_state.model_params
            )
            
            return response
            
        except Exception as e:
            logger.error("Error processing chat message: %s", e)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _save_conversation_message(self, role: str, content: str):
        """Save message to current conversation."""
        if st.session_state.current_conversation_id:
            self.conversation_manager.add_message(
                st.session_state.current_conversation_id,
                role,
                content            )
    
    def _create_new_conversation(self, first_message: Optional[str] = None) -> Optional[int]:
        """Create a new conversation."""
        title = generate_conversation_title(first_message) if first_message else "New Conversation"
        
        conversation = self.conversation_manager.create_conversation(
            title=title,
            provider=st.session_state.ai_provider,
            system_prompt=st.session_state.system_prompt
        )
        
        return conversation.id if conversation else None
    
    def _render_main_interface(self):
        """Render the main chat interface."""
        # Check if diagnostics panel should be shown
        if st.session_state.get("show_diagnostics", False):
            st.title("🏥 FleetPulse System Diagnostics")
            
            # Back button
            if st.button("← Back to Chat"):
                st.session_state.show_diagnostics = False
                st.rerun()
            
            # Render full diagnostic panel
            render_diagnostic_panel()
            return
          # Header with intelligent expert selection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title("🚀 FleetPulse GenAI Chatbot")
        
        with col2:
            # Provider selection
            available_providers = [p.value for p in get_available_providers()]
            if available_providers:
                st.session_state.ai_provider = render_provider_selector(
                    available_providers, 
                    st.session_state.ai_provider
                )
        
        # Smart Expert Selection Panel
        # Get the current user input from session state if available
        current_input = st.session_state.get("current_user_input", "")
        
        # Get conversation history for context
        conversation_history = []
        if st.session_state.current_conversation_id:
            stored_messages = self.conversation_manager.get_chat_history(st.session_state.current_conversation_id)
            conversation_history = [{"role": msg.role, "content": msg.content} for msg in stored_messages[-5:]]  # Last 5 messages for context
        
        # Render intelligent expert selection panel
        st.session_state.system_prompt = render_smart_expert_panel(
            user_input=current_input,
            conversation_history=conversation_history,
            current_expert=st.session_state.system_prompt,
            show_insights=st.session_state.get("show_expert_insights", False)
        )
        
        # Action buttons row
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Dashboard toggle
            if st.button("📊 Toggle Dashboard", key="dashboard_toggle"):
                st.session_state.show_dashboard = not st.session_state.show_dashboard
        
        with col2:
            # Diagnostics button
            if st.button("🏥 System Diagnostics", key="diagnostics_toggle"):
                st.session_state.show_diagnostics = True
                st.rerun()
        
        with col3:
            # Quick health check
            if st.button("🔍 Quick Health Check", key="health_check"):
                with st.spinner("Checking system health..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            results = loop.run_until_complete(self._run_system_diagnostics())
                            if results:
                                error_count = sum(1 for r in results if r.status == "error")
                                if error_count > 0:
                                    st.error(f"⚠️ {error_count} issues detected")
                                else:
                                    st.success("✅ All systems healthy")
                            else:
                                st.warning("Unable to run diagnostics")
                        finally:
                            loop.close()
                    except Exception as e:
                        st.error(f"Health check failed: {str(e)}")
        
        # Show dashboard if enabled
        if st.session_state.show_dashboard:
            with st.expander("📊 Fleet Dashboard", expanded=True):
                try:
                    run_dashboard_async(self.fleet_dashboard.render_overview_dashboard)
                except Exception as e:
                    st.error(f"Dashboard error: {e}")
        
        # Chat interface
        if not st.session_state.messages and not st.session_state.current_conversation_id:
            # Show welcome screen for new users
            action = render_welcome_screen()
            if action:
                st.session_state.user_input = action
                st.rerun()
        else:
            # Display conversation messages
            for message in st.session_state.messages:
                render_chat_message(message)
            
            # Display messages from current conversation
            if st.session_state.current_conversation_id:
                stored_messages = self.conversation_manager.get_chat_history(st.session_state.current_conversation_id)
                for message in stored_messages:
                    if message.role != "system":  # Don't show system prompts
                        render_chat_message(message)
          # Chat input
        if prompt := st.chat_input("Ask me anything about your fleet..."):
            self._handle_user_input(prompt)
    
    def _handle_user_input(self, user_input: str):
        """Handle user input and generate response."""
        # Store current input for expert routing
        st.session_state.current_user_input = user_input
        
        # Create new conversation if needed
        if not st.session_state.current_conversation_id:
            st.session_state.current_conversation_id = self._create_new_conversation(user_input)
        
        # Add user message to display
        user_message = ChatMessage(role="user", content=user_input, timestamp=datetime.now().isoformat())
        st.session_state.messages.append(user_message)
        
        # Save to conversation
        self._save_conversation_message("user", user_input)
        
        # Display user message
        render_chat_message(user_message)
        
        # Process and get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use asyncio to run async function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(self._process_chat_message(user_input))
                    loop.close()
                    
                    # Display response
                    st.write(response)
                    
                    # Add to session state and save
                    assistant_message = ChatMessage(
                        role="assistant", 
                        content=response, 
                        timestamp=datetime.now().isoformat()
                    )
                    st.session_state.messages.append(assistant_message)
                    self._save_conversation_message("assistant", response)                    
                except Exception as e:
                    error_msg = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_msg)
                    logger.error("Error in chat processing: %s", e)
    
    def _render_sidebar(self):
        """Render sidebar with configuration and conversation history."""
        with st.sidebar:
            # System status
            status = self._check_system_status()
            render_status_indicators(status["genai"], status["mcp"], status["fleetpulse"])
            
            # MCP Tool status indicator
            if self.mcp_client:
                render_tool_status_indicator(self.mcp_client)
              # Configuration panel
            st.session_state.model_params = render_configuration_panel()
            
            # Expert Routing Configuration
            with st.expander("🧠 Expert Routing Settings", expanded=False):
                st.session_state.show_expert_insights = st.checkbox(
                    "Show Expert Routing Analysis",
                    value=st.session_state.get("show_expert_insights", False),
                    help="Display detailed analysis of how the system selects experts"
                )
                
                if st.button("🔄 Reset Expert Selection"):
                    st.session_state.system_prompt = "general"
                    st.session_state.current_user_input = ""
                    st.success("Expert selection reset to General Assistant")
            
            # Diagnostic and Recovery Section
            with st.expander("🏥 System Diagnostics", expanded=False):
                if st.button("🔍 Run Diagnostics"):
                    with st.spinner("Running diagnostics..."):
                        diagnostic_results = asyncio.run(self._run_system_diagnostics())
                        if diagnostic_results:
                            st.session_state.diagnostic_results = diagnostic_results
                            st.success(f"Diagnostics completed - {len(diagnostic_results)} checks run")
                        else:
                            st.warning("Diagnostic runner failed")
                
                # Quick recovery panel
                if self.mcp_client:
                    render_quick_recovery_panel(self.mcp_client)
            
            # Show latest diagnostic results if available
            if hasattr(st.session_state, 'diagnostic_results') and st.session_state.diagnostic_results:
                with st.expander("📋 Latest Diagnostic Results", expanded=False):
                    results = st.session_state.diagnostic_results
                    healthy_count = sum(1 for r in results if r.status == "healthy")
                    error_count = sum(1 for r in results if r.status == "error")
                    
                    if error_count > 0:
                        st.error(f"⚠️ {error_count} issues detected")
                    else:
                        st.success(f"✅ All {healthy_count} checks passed")
                    
                    if st.button("📄 View Full Report"):
                        # This would open the full diagnostic panel in main area
                        st.session_state.show_diagnostics = True
                        st.rerun()
            
            # Conversation management
            conversations = self.conversation_manager.list_conversations(limit=20)
            
            # Convert to format expected by sidebar component
            conversation_list = []
            for conv in conversations:
                conversation_list.append({
                    "id": conv.id,
                    "title": conv.title,
                    "updated_at": format_timestamp(conv.updated_at) if conv.updated_at else "Unknown"
                })
            
            selected_conv = render_conversation_sidebar(
                conversation_list, 
                st.session_state.current_conversation_id
            )
            
            # Handle conversation selection
            if selected_conv == "new":
                # Clear current conversation
                st.session_state.current_conversation_id = None
                st.session_state.messages = []
                st.session_state.tools_used = []
                st.rerun()
            elif selected_conv != st.session_state.current_conversation_id:
                # Load selected conversation
                st.session_state.current_conversation_id = selected_conv
                st.session_state.messages = []
                st.session_state.tools_used = []
                st.rerun()
            
            # Tools used display
            if st.session_state.tools_used:
                from ui.components import render_tool_usage_display
                render_tool_usage_display(st.session_state.tools_used)
            
            # Error handling guidance
            if any(not tool.get("success", True) for tool in st.session_state.tools_used):
                with st.expander("🛠️ Error Recovery", expanded=True):
                    st.warning("Some tools have failed. Check the main chat for detailed error information.")
                    if st.button("🔄 Reset All Tools"):
                        # Reset tool errors
                        st.session_state.tools_used = []
                        if self.mcp_client:
                            # Reinitialize MCP client
                            st.session_state.mcp_client = type(self.mcp_client)()
                        st.rerun()
    
    async def _ai_driven_tool_selection(self, user_message: str) -> List[Dict[str, Any]]:
        """Use AI to intelligently select which tools to call based on user intent."""
        try:
            # Create a specialized prompt for tool selection
            tool_selection_prompt = f"""
            You are a tool selection specialist for FleetPulse fleet management.
            
            Available tools:
            1. get_fleet_status - Get overall fleet health and status summary
            2. get_host_details - Get detailed information about a specific host (requires hostname)
            3. get_update_history - Get package update history (requires hostname, optional days parameter)
            4. get_pending_updates - Get list of systems with pending updates (optional severity filter)
            5. schedule_updates - Schedule update operations (requires hostnames and schedule)
            6. generate_fleet_report - Generate comprehensive fleet reports
            7. get_system_metrics - Get system performance metrics (requires hostname)
            8. check_package_info - Get package information (requires package_name)
            
            User query: "{user_message}"
            
            Based on the user's query, determine which tools should be called to provide a complete answer.
            Consider that:
            - Questions about "hosts", "servers", or "fleet" often need get_fleet_status first
            - Questions about specific hosts need get_host_details
            - Questions about "updates" with time references need get_update_history
            - Questions about current update status need get_pending_updates
            - Multiple tools may be needed for comprehensive answers
            
            Respond with a JSON array of tool names that should be called:
            ["tool1", "tool2", ...]
            
            If no tools are needed, respond with: []
            """
              # Use a simple AI call to determine tools
            if not self.genai_manager:
                logger.warning("GenAI manager not available for tool selection")
                return []
            
            provider = GenAIProvider(st.session_state.ai_provider)
            messages = [ChatMessage(role="system", content=tool_selection_prompt)]
            
            response = await self.genai_manager.chat_completion(
                messages,
                provider=provider,
                temperature=0.1,  # Low temperature for consistent tool selection
                max_tokens=100
            )
            
            # Parse the response
            import json
            import re
            
            # Extract JSON from potential markdown code blocks
            response_cleaned = response.strip()
            
            # Try to extract JSON from markdown code blocks
            # Pattern matches ```json\n...``` or ```\n...```
            markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
            match = re.search(markdown_pattern, response_cleaned, re.DOTALL)
            
            if match:
                json_content = match.group(1).strip()
            else:
                json_content = response_cleaned
            
            try:
                tool_names = json.loads(json_content)
                if isinstance(tool_names, list):
                    return [{"name": tool_name, "keywords": ["ai_selected"]} for tool_name in tool_names]
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI tool selection response: %s", response)
            
            return []
            
        except Exception as e:
            logger.error("Error in AI-driven tool selection: %s", e)
            # Fall back to keyword detection
            return await self._detect_tool_usage(user_message)

    # ...existing code...
    def run(self):
        """Run the main application."""
        try:
            self._initialize_session_state()
            # Ensure async components are initialized
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_initialize_components())
            loop.close()
            # Render sidebar
            self._render_sidebar()
            # Render main interface
            self._render_main_interface()
        except Exception as e:
            logger.error("Application error: %s", e)
            render_error_message(
                str(e),
                "Please check your configuration and try refreshing the page."
            )


def main():
    """Main application entry point."""
    try:
        # Initialize and run chatbot
        chatbot = FleetPulseChatbot()
        chatbot.run()
        
    except Exception as e:
        logger.error("Failed to start application: %s", e)
        st.error(f"Failed to start FleetPulse Chatbot: {e}")
        
        st.markdown("""
        ### Troubleshooting
        
        1. **Check Environment Variables**: Ensure you have configured at least one AI provider
        2. **Database Issues**: Check if the SQLite database can be created/accessed
        3. **Network Connectivity**: Verify access to AI provider APIs and FleetPulse backend
        4. **Dependencies**: Ensure all required packages are installed
        
        **Environment Variables Required:**
        - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY` (at least one)
        - `FLEETPULSE_API_URL` (default: http://localhost:8000)
        """)


if __name__ == "__main__":
    main()