"""Tests for GenAI Manager functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from core.genai_manager import GenAIManager, ChatMessage, OpenAIProvider


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('core.genai_manager.get_settings') as mock:
        mock.return_value.openai_api_key = "test-key"
        mock.return_value.genai_provider = "openai"
        yield mock.return_value


@pytest.fixture
def genai_manager(mock_settings):
    """Create GenAI manager instance for testing."""
    return GenAIManager()


class TestChatMessage:
    """Test ChatMessage dataclass."""
    
    def test_chat_message_creation(self):
        """Test creating a chat message."""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.timestamp is None
    
    def test_chat_message_with_timestamp(self):
        """Test creating a chat message with timestamp."""
        timestamp = "2024-01-01T00:00:00"
        message = ChatMessage(role="assistant", content="Hi", timestamp=timestamp)
        assert message.timestamp == timestamp


class TestGenAIManager:
    """Test GenAI Manager functionality."""
    
    def test_initialization(self, genai_manager):
        """Test GenAI manager initialization."""
        assert genai_manager is not None
        assert hasattr(genai_manager, 'providers')
        assert hasattr(genai_manager, 'settings')
    
    def test_get_available_providers(self, genai_manager):
        """Test getting available providers."""
        providers = genai_manager.get_available_providers()
        assert isinstance(providers, list)
    
    @pytest.mark.asyncio
    async def test_chat_completion_no_provider(self, genai_manager):
        """Test chat completion with unavailable provider."""
        messages = [ChatMessage(role="user", content="Test")]
        
        with pytest.raises(ValueError, match="Provider .* not available"):
            await genai_manager.chat_completion(messages, provider="invalid")


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def openai_provider(self):
        """Create OpenAI provider for testing."""
        with patch('semantic_kernel.Kernel'), \
             patch('semantic_kernel.connectors.ai.open_ai.OpenAIChatCompletion'):
            return OpenAIProvider("test-key")
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, openai_provider):
        """Test OpenAI chat completion."""
        messages = [ChatMessage(role="user", content="Hello")]
        
        # Mock the chat service response
        with patch.object(openai_provider, 'chat_service') as mock_service:
            mock_response = Mock()
            mock_response.content = "Hello there!"
            mock_service.get_chat_message_content = AsyncMock(return_value=mock_response)
            
            response = await openai_provider.chat_completion(messages)
            assert response == "Hello there!"
    
    @pytest.mark.asyncio
    async def test_stream_completion(self, openai_provider):
        """Test OpenAI streaming completion."""
        messages = [ChatMessage(role="user", content="Hello")]
        
        # Mock the streaming response
        async def mock_stream():
            chunks = ["Hello", " there", "!"]
            for chunk in chunks:
                mock_chunk = Mock()
                mock_chunk.content = chunk
                yield mock_chunk
        
        with patch.object(openai_provider, 'chat_service') as mock_service:
            mock_service.get_streaming_chat_message_content = mock_stream
            
            result = []
            async for chunk in openai_provider.stream_completion(messages):
                result.append(chunk)
            
            assert "".join(result) == "Hello there!"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in providers."""
    provider = OpenAIProvider("test-key")
    messages = [ChatMessage(role="user", content="Test")]
    
    with patch.object(provider, 'chat_service') as mock_service:
        mock_service.get_chat_message_content = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception, match="API Error"):
            await provider.chat_completion(messages)


def test_message_conversion():
    """Test converting messages between formats."""
    messages = [
        ChatMessage(role="system", content="You are helpful"),
        ChatMessage(role="user", content="Hello"),
        ChatMessage(role="assistant", content="Hi there!")
    ]
    
    # Test that messages can be processed
    assert len(messages) == 3
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert messages[2].role == "assistant"