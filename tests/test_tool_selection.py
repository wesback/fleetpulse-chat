"""Tests for AI tool selection parsing functionality."""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from app import FleetPulseChatbot


class TestAIToolSelection:
    """Test AI tool selection parsing logic."""
    
    @pytest.fixture
    def chatbot(self):
        """Create a FleetPulseChatbot instance for testing."""
        with patch('app.GenAIManager'), \
             patch('app.FleetPulseMCPClient'), \
             patch('app.ConversationManager'), \
             patch('app.FleetDashboard'):
            return FleetPulseChatbot()
    
    @pytest.mark.asyncio
    async def test_parse_plain_json_array(self, chatbot):
        """Test parsing plain JSON array response."""
        # Mock the genai_manager to return plain JSON
        mock_genai_manager = Mock()
        mock_genai_manager.chat_completion = AsyncMock(return_value='["get_host_details", "get_update_history"]')
        chatbot.genai_manager = mock_genai_manager
        
        # Call the method
        with patch('streamlit.session_state', {'ai_provider': 'openai'}):
            result = await chatbot._ai_driven_tool_selection("Tell me about homeserver")
        
        # Verify the result
        expected = [
            {"name": "get_host_details", "keywords": ["ai_selected"]},
            {"name": "get_update_history", "keywords": ["ai_selected"]}
        ]
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_parse_markdown_wrapped_json(self, chatbot):
        """Test parsing JSON wrapped in markdown code blocks."""
        # Mock the genai_manager to return markdown-wrapped JSON (the current issue)
        mock_genai_manager = Mock()
        mock_genai_manager.chat_completion = AsyncMock(return_value='```json\n["get_host_details", "get_update_history"]\n```')
        chatbot.genai_manager = mock_genai_manager
        
        # Call the method - patch the session state and GenAIProvider
        with patch('app.st.session_state', {'ai_provider': 'openai'}), \
             patch('app.GenAIProvider') as mock_provider_class:
            mock_provider_class.return_value = 'openai'
            result = await chatbot._ai_driven_tool_selection("Tell me about homeserver")
        
        # Verify the result - this should pass after our fix
        expected = [
            {"name": "get_host_details", "keywords": ["ai_selected"]},
            {"name": "get_update_history", "keywords": ["ai_selected"]}
        ]
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_parse_markdown_wrapped_json_with_whitespace(self, chatbot):
        """Test parsing JSON wrapped in markdown with extra whitespace."""
        # Mock the genai_manager to return markdown-wrapped JSON with whitespace
        mock_genai_manager = Mock()
        mock_genai_manager.chat_completion = AsyncMock(return_value='  ```json  \n["get_fleet_status"]\n```  ')
        chatbot.genai_manager = mock_genai_manager
        
        # Call the method
        with patch('streamlit.session_state', {'ai_provider': 'openai'}):
            result = await chatbot._ai_driven_tool_selection("What's my fleet status?")
        
        # Verify the result
        expected = [{"name": "get_fleet_status", "keywords": ["ai_selected"]}]
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_parse_empty_array(self, chatbot):
        """Test parsing empty JSON array."""
        # Mock the genai_manager to return empty array
        mock_genai_manager = Mock()
        mock_genai_manager.chat_completion = AsyncMock(return_value='[]')
        chatbot.genai_manager = mock_genai_manager
        
        # Call the method
        with patch('streamlit.session_state', {'ai_provider': 'openai'}):
            result = await chatbot._ai_driven_tool_selection("Just a general question")
        
        # Verify the result
        assert result == []
    
    @pytest.mark.asyncio
    async def test_parse_invalid_json_fallback(self, chatbot):
        """Test fallback to keyword detection when JSON parsing fails."""
        # Mock the genai_manager to return invalid JSON
        mock_genai_manager = Mock()
        mock_genai_manager.chat_completion = AsyncMock(return_value='This is not JSON at all')
        chatbot.genai_manager = mock_genai_manager
        
        # Mock the fallback method
        chatbot._detect_tool_usage = AsyncMock(return_value=[{"name": "fallback_tool", "keywords": ["detected"]}])
        
        # Call the method
        with patch('streamlit.session_state', {'ai_provider': 'openai'}):
            result = await chatbot._ai_driven_tool_selection("Tell me about homeserver")
        
        # Verify fallback was called
        chatbot._detect_tool_usage.assert_called_once_with("Tell me about homeserver")
        assert result == [{"name": "fallback_tool", "keywords": ["detected"]}]
    
    @pytest.mark.asyncio
    async def test_parse_non_array_json_fallback(self, chatbot):
        """Test fallback when JSON is valid but not an array."""
        # Mock the genai_manager to return valid JSON but not an array
        mock_genai_manager = Mock()
        mock_genai_manager.chat_completion = AsyncMock(return_value='{"tool": "get_host_details"}')
        chatbot.genai_manager = mock_genai_manager
        
        # Mock the fallback method
        chatbot._detect_tool_usage = AsyncMock(return_value=[])
        
        # Call the method
        with patch('streamlit.session_state', {'ai_provider': 'openai'}):
            result = await chatbot._ai_driven_tool_selection("Tell me about homeserver")
        
        # Verify fallback was called and returns empty array
        chatbot._detect_tool_usage.assert_called_once_with("Tell me about homeserver")
        assert result == []


def test_json_extraction_helper():
    """Test the JSON extraction logic in isolation."""
    # This will test the helper function we'll create to extract JSON from markdown
    
    # Test cases with various markdown wrapping formats
    test_cases = [
        ('["tool1", "tool2"]', ["tool1", "tool2"]),  # Plain JSON
        ('```json\n["tool1", "tool2"]\n```', ["tool1", "tool2"]),  # Markdown wrapped
        ('```\n["tool1", "tool2"]\n```', ["tool1", "tool2"]),  # Simple code block
        ('  ```json  \n["tool1"]\n```  ', ["tool1"]),  # Extra whitespace
        ('```json\n[]\n```', []),  # Empty array
        ('invalid json', None),  # Invalid JSON should return None
        ('```json\n{"not": "array"}\n```', None),  # Valid JSON but not array
    ]
    
    # We'll implement extract_json_from_response helper function
    for response, expected in test_cases:
        result = extract_json_from_response(response)
        assert result == expected, f"Failed for input: {response}"


def extract_json_from_response(response: str):
    """Helper function to extract JSON from markdown-wrapped response.
    
    This function will be integrated into the main codebase.
    """
    import json
    import re
    
    # Strip whitespace
    response = response.strip()
    
    # Try to extract JSON from markdown code blocks
    # Pattern matches ```json\n...``` or ```\n...```
    markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(markdown_pattern, response, re.DOTALL)
    
    if match:
        json_content = match.group(1).strip()
    else:
        json_content = response
    
    try:
        parsed = json.loads(json_content)
        # Only return if it's a list
        if isinstance(parsed, list):
            return parsed
        else:
            return None
    except json.JSONDecodeError:
        return None