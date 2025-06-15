"""Tests for UI components functionality."""

import pytest
from unittest.mock import Mock, patch
import streamlit as st
from core.genai_manager import ChatMessage
from core.mcp_client import MCPToolResult
from ui.components import (
    render_provider_selector,
    render_prompt_selector,
    generate_conversation_title,
    render_fleet_status_card,
    render_host_details_card
)


class TestUIComponents:
    """Test UI component functions."""
    
    @patch('streamlit.selectbox')
    def test_render_provider_selector(self, mock_selectbox):
        """Test provider selector rendering."""
        mock_selectbox.return_value = "openai"
        
        available_providers = ["openai", "anthropic"]
        current_provider = "openai"
        
        result = render_provider_selector(available_providers, current_provider)
        
        assert result == "openai"
        mock_selectbox.assert_called_once()
    
    @patch('streamlit.selectbox')
    @patch('streamlit.expander')
    def test_render_prompt_selector(self, mock_expander, mock_selectbox):
        """Test prompt selector rendering."""
        mock_selectbox.return_value = "linux_admin"
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        
        result = render_prompt_selector("general")
        
        assert result == "linux_admin"
        mock_selectbox.assert_called_once()
    
    @patch('streamlit.selectbox')
    def test_render_provider_selector_empty(self, mock_selectbox):
        """Test provider selector with no available providers."""
        with patch('streamlit.error') as mock_error:
            result = render_provider_selector([], "openai")
            
            mock_error.assert_called_once()
            assert result == "openai"  # Should return current provider as fallback


class TestChatMessage:
    """Test chat message rendering."""
    
    @patch('streamlit.chat_message')
    @patch('streamlit.write')
    @patch('streamlit.caption')
    def test_render_chat_message_with_timestamp(self, mock_caption, mock_write, mock_chat_message):
        """Test rendering chat message with timestamp."""
        from ui.components import render_chat_message
        
        mock_chat_message.return_value.__enter__ = Mock()
        mock_chat_message.return_value.__exit__ = Mock()
        
        message = ChatMessage(
            role="user",
            content="Hello",
            timestamp="2024-01-01T10:00:00"
        )
        
        render_chat_message(message, show_timestamp=True)
        
        mock_chat_message.assert_called_once_with("user")
        mock_write.assert_called_once_with("Hello")
        mock_caption.assert_called_once()
    
    @patch('streamlit.chat_message')
    @patch('streamlit.write')
    @patch('streamlit.caption')
    def test_render_chat_message_without_timestamp(self, mock_caption, mock_write, mock_chat_message):
        """Test rendering chat message without timestamp."""
        from ui.components import render_chat_message
        
        mock_chat_message.return_value.__enter__ = Mock()
        mock_chat_message.return_value.__exit__ = Mock()
        
        message = ChatMessage(role="assistant", content="Hi there")
        
        render_chat_message(message, show_timestamp=False)
        
        mock_chat_message.assert_called_once_with("assistant")
        mock_write.assert_called_once_with("Hi there")
        mock_caption.assert_not_called()


class TestMCPToolResult:
    """Test MCP tool result rendering."""
    
    @patch('streamlit.expander')
    @patch('streamlit.columns')
    @patch('streamlit.write')
    @patch('streamlit.json')
    def test_render_mcp_tool_result_success(self, mock_json, mock_write, mock_columns, mock_expander):
        """Test rendering successful tool result."""
        from ui.components import render_mcp_tool_result
        
        # Mock the expander and columns
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        mock_columns.return_value = [Mock(), Mock()]
        
        result = MCPToolResult(
            success=True,
            data={"status": "ok", "hosts": 10}
        )
        
        render_mcp_tool_result("get_fleet_status", result)
        
        mock_expander.assert_called_once()
        mock_json.assert_called_once_with({"status": "ok", "hosts": 10})
    
    @patch('streamlit.expander')
    @patch('streamlit.columns')
    @patch('streamlit.error')
    def test_render_mcp_tool_result_error(self, mock_error, mock_columns, mock_expander):
        """Test rendering failed tool result."""
        from ui.components import render_mcp_tool_result
        
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        mock_columns.return_value = [Mock(), Mock()]
        
        result = MCPToolResult(
            success=False,
            data=None,
            error="API connection failed"
        )
        
        render_mcp_tool_result("get_fleet_status", result, expanded=True)
        
        mock_expander.assert_called_once()
        mock_error.assert_called_once_with("Error: API connection failed")


class TestFleetStatusCard:
    """Test fleet status card rendering."""
    
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.progress')
    @patch('streamlit.caption')
    def test_render_fleet_status_card(self, mock_caption, mock_progress, mock_metric, 
                                    mock_columns, mock_subheader):
        """Test fleet status card rendering."""
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        
        fleet_data = {
            "total_hosts": 100,
            "healthy_hosts": 85,
            "pending_updates": 15,
            "critical_issues": 2
        }
        
        render_fleet_status_card(fleet_data)
        
        mock_subheader.assert_called_once()
        mock_columns.assert_called_once_with(4)
        assert mock_metric.call_count == 4  # Called for each metric
        mock_progress.assert_called_once()
        mock_caption.assert_called_once()


class TestHostDetailsCard:
    """Test host details card rendering."""
    
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.write')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    def test_render_host_details_card_up_to_date(self, mock_warning, mock_success, 
                                                mock_write, mock_columns, mock_subheader):
        """Test host details card for up-to-date host."""
        mock_columns.return_value = [Mock(), Mock()]
        
        host_data = {
            "hostname": "web-server-01",
            "os": "Ubuntu 22.04",
            "kernel": "5.15.0-generic",
            "uptime": "15 days",
            "last_seen": "2 minutes ago",
            "packages_installed": 500,
            "updates_available": 0,
            "security_updates": 0
        }
        
        render_host_details_card(host_data)
        
        mock_subheader.assert_called_once()
        mock_success.assert_called_once_with("System up to date")
        mock_warning.assert_not_called()
    
    @patch('streamlit.subheader')
    @patch('streamlit.columns') 
    @patch('streamlit.write')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    def test_render_host_details_card_updates_available(self, mock_warning, mock_success,
                                                       mock_write, mock_columns, mock_subheader):
        """Test host details card for host with updates."""
        mock_columns.return_value = [Mock(), Mock()]
        
        host_data = {
            "hostname": "db-server-02",
            "os": "CentOS 8",
            "kernel": "4.18.0-generic",
            "uptime": "45 days",
            "last_seen": "1 minute ago",
            "packages_installed": 650,
            "updates_available": 12,
            "security_updates": 3
        }
        
        render_host_details_card(host_data)
        
        mock_subheader.assert_called_once()
        mock_warning.assert_called_once_with("Updates available")
        mock_success.assert_not_called()


class TestWelcomeScreen:
    """Test welcome screen rendering."""
    
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    def test_render_welcome_screen(self, mock_button, mock_columns, mock_subheader, 
                                 mock_markdown, mock_title):
        """Test welcome screen rendering."""
        from ui.components import render_welcome_screen
        
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        mock_button.return_value = False
        
        result = render_welcome_screen()
        
        mock_title.assert_called_once()
        mock_markdown.assert_called()
        mock_subheader.assert_called()
        assert result is None  # No button clicked
    
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    def test_render_welcome_screen_button_click(self, mock_button, mock_columns, 
                                              mock_subheader, mock_markdown, mock_title):
        """Test welcome screen with button click."""
        from ui.components import render_welcome_screen
        
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        
        # Mock first button to return True
        mock_button.side_effect = [True, False, False]
        
        result = render_welcome_screen()
        
        assert result == "check_fleet_status"


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_generate_conversation_title_simple(self):
        """Test generating conversation title from simple message."""
        from utils.helpers import generate_conversation_title
        
        message = "What is the status of my fleet?"
        title = generate_conversation_title(message)
        
        assert "status" in title.lower()
        assert len(title) <= 50
    
    def test_generate_conversation_title_with_prefix(self):
        """Test generating title with common prefix removal."""
        from utils.helpers import generate_conversation_title
        
        message = "Can you help me check the fleet status?"
        title = generate_conversation_title(message)
        
        # Should remove "can you" prefix
        assert not title.lower().startswith("can you")
        assert "check" in title.lower()
    
    def test_generate_conversation_title_long_message(self):
        """Test generating title from long message."""
        from utils.helpers import generate_conversation_title
        
        long_message = "This is a very long message that should be truncated to a reasonable length for the conversation title"
        title = generate_conversation_title(long_message, max_length=30)
        
        assert len(title) <= 33  # 30 + "..." = 33
        assert title.endswith("...")
    
    def test_generate_conversation_title_empty_message(self):
        """Test generating title from empty message."""
        from utils.helpers import generate_conversation_title
        
        title = generate_conversation_title("")
        assert title == "New Conversation"
        
        title = generate_conversation_title("   ")
        assert title == "New Conversation"


@pytest.mark.integration
class TestUIIntegration:
    """Integration tests for UI components."""
    
    def test_component_integration(self):
        """Test that components work together."""
        # This would test actual Streamlit integration
        # For now, just test that imports work
        from ui.components import (
            render_provider_selector,
            render_prompt_selector,
            render_chat_message,
            render_mcp_tool_result
        )
        
        assert callable(render_provider_selector)
        assert callable(render_prompt_selector)
        assert callable(render_chat_message)
        assert callable(render_mcp_tool_result)