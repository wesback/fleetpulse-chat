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
from config.prompts import get_system_prompt, get_prompt_descriptions
from core.genai_manager import GenAIManager, ChatMessage
from core.mcp_client import FleetPulseMCPClient
from core.conversation import ConversationManager

# UI imports
from ui.components import (
    render_provider_selector, render_prompt_selector, render_chat_message,
    render_mcp_tool_result, render_configuration_panel, render_conversation_sidebar,
    render_welcome_screen, render_error_message, render_status_indicators
)
from ui.dashboard import FleetDashboard, run_dashboard_async

# Utils imports
from utils.helpers import setup_logging, generate_conversation_title, format_timestamp
from utils.validators import sanitize_input, validate_mcp_tool_parameters, ValidationError


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
        self.conversation_manager = None
        self.fleet_dashboard = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize core components."""
        try:
            self.genai_manager = GenAIManager()
            self.mcp_client = FleetPulseMCPClient()
            self.conversation_manager = ConversationManager()
            self.fleet_dashboard = FleetDashboard()
            logger.info("Components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
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
        
        if "tools_used" not in st.session_state:
            st.session_state.tools_used = []
        
        if "model_params" not in st.session_state:
            st.session_state.model_params = {"temperature": 0.7, "max_tokens": 2000}
        
        if "show_dashboard" not in st.session_state:
            st.session_state.show_dashboard = False
    
    def _check_system_status(self) -> Dict[str, bool]:
        """Check status of system components."""
        status = {
            "genai": bool(self.genai_manager and self.genai_manager.get_available_providers()),
            "mcp": bool(self.mcp_client),
            "fleetpulse": True  # Would check actual API connectivity
        }
        return status
    
    async def _detect_tool_usage(self, user_message: str) -> List[Dict[str, Any]]:
        """Detect if user message suggests tool usage."""
        tools_to_try = []
        message_lower = user_message.lower()
        
        # Simple keyword-based detection
        tool_keywords = {
            "get_fleet_status": ["fleet status", "overall status", "fleet health", "fleet overview"],
            "get_host_details": ["host details", "server info", "host info", "system details"],
            "get_pending_updates": ["pending updates", "available updates", "updates needed"],
            "get_update_history": ["update history", "update log", "previous updates"],
            "generate_fleet_report": ["generate report", "fleet report", "create report"],
            "get_system_metrics": ["system metrics", "performance", "cpu usage", "memory usage"]
        }
        
        for tool_name, keywords in tool_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                tools_to_try.append({"name": tool_name, "keywords": keywords})
        
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
                
                # Execute tool
                result = await self.mcp_client.execute_tool(tool_name, validated_params)
                
                tool_results.append({
                    "name": tool_name,
                    "parameters": validated_params,
                    "result": result.data if result.success else None,
                    "success": result.success,
                    "error": result.error
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
                logger.warning(f"Parameter validation failed for {tool_name}: {e}")
                tool_results.append({
                    "name": tool_name,
                    "parameters": {},
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
            except Exception as e:
                logger.error(f"Tool execution failed for {tool_name}: {e}")
                tool_results.append({
                    "name": tool_name,
                    "parameters": {},
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
        
        return tool_results
    
    def _extract_tool_parameters(self, tool_name: str, message: str) -> Dict[str, Any]:
        """Extract parameters for tools from user message (simplified)."""
        import re
        
        params = {}
        
        # Extract hostnames
        hostname_pattern = r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\b'
        hostnames = re.findall(hostname_pattern, message)
        
        if tool_name in ["get_host_details", "get_update_history", "get_system_metrics"]:
            if hostnames:
                params["hostname"] = hostnames[0]
        
        if tool_name == "schedule_updates":
            if hostnames:
                params["hostnames"] = hostnames
        
        # Extract days for history
        if tool_name == "get_update_history":
            day_match = re.search(r'(\d+)\s*days?', message)
            if day_match:
                params["days"] = int(day_match.group(1))
        
        # Extract severity
        if tool_name == "get_pending_updates":
            severity_match = re.search(r'(critical|high|important|medium|moderate|low)', message.lower())
            if severity_match:
                params["severity"] = severity_match.group(1)
        
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
            
            # Check for tool usage
            suggested_tools = await self._detect_tool_usage(user_message)
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
            logger.error(f"Error processing chat message: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _save_conversation_message(self, role: str, content: str):
        """Save message to current conversation."""
        if st.session_state.current_conversation_id:
            self.conversation_manager.add_message(
                st.session_state.current_conversation_id,
                role,
                content
            )
    
    def _create_new_conversation(self, first_message: Optional[str] = None) -> int:
        """Create a new conversation."""
        title = generate_conversation_title(first_message) if first_message else "New Conversation"
        
        conversation = self.conversation_manager.create_conversation(
            title=title,
            provider=st.session_state.ai_provider,
            system_prompt=st.session_state.system_prompt
        )
        
        return conversation.id
    
    def _render_main_interface(self):
        """Render the main chat interface."""
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        
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
        
        with col3:
            # System prompt selection
            st.session_state.system_prompt = render_prompt_selector(st.session_state.system_prompt)
        
        # Dashboard toggle
        if st.button("📊 Toggle Dashboard", key="dashboard_toggle"):
            st.session_state.show_dashboard = not st.session_state.show_dashboard
        
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
                    logger.error(f"Error in chat processing: {e}")
    
    def _render_sidebar(self):
        """Render sidebar with configuration and conversation history."""
        with st.sidebar:
            # System status
            status = self._check_system_status()
            render_status_indicators(status["genai"], status["mcp"], status["fleetpulse"])
            
            # Configuration panel
            st.session_state.model_params = render_configuration_panel()
            
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
    
    def run(self):
        """Run the main application."""
        try:
            self._initialize_session_state()
            
            # Render sidebar
            self._render_sidebar()
            
            # Render main interface
            self._render_main_interface()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
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
        logger.error(f"Failed to start application: {e}")
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