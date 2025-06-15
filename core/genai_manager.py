"""GenAI Manager for coordinating multiple AI providers using Semantic Kernel."""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncIterator, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import KernelArguments

from config import GenAIProvider, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str
    content: str
    timestamp: Optional[str] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> str:
        """Standard interface for all providers."""
        pass
    
    @abstractmethod
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Streaming interface."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.kernel = sk.Kernel()
        self.chat_service = OpenAIChatCompletion(
            service_id="openai_chat",
            api_key=api_key,
            ai_model_id="gpt-4"
        )
        self.kernel.add_service(self.chat_service)
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> str:
        """Get chat completion from OpenAI."""
        try:
            # Convert messages to SK format
            chat_history = sk.ChatHistory()
            for msg in messages:
                if msg.role == "user":
                    chat_history.add_user_message(msg.content)
                elif msg.role == "assistant":
                    chat_history.add_assistant_message(msg.content)
                elif msg.role == "system":
                    chat_history.add_system_message(msg.content)
            
            # Get response
            response = await self.chat_service.get_chat_message_content(
                chat_history=chat_history,
                settings=sk.connectors.ai.open_ai.OpenAIChatRequestSettings(
                    max_tokens=kwargs.get("max_tokens", 2000),
                    temperature=kwargs.get("temperature", 0.7)
                )
            )
            
            return str(response.content)
        
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat completion from OpenAI."""
        try:
            # Convert messages to SK format
            chat_history = sk.ChatHistory()
            for msg in messages:
                if msg.role == "user":
                    chat_history.add_user_message(msg.content)
                elif msg.role == "assistant":
                    chat_history.add_assistant_message(msg.content)
                elif msg.role == "system":
                    chat_history.add_system_message(msg.content)
            
            # Stream response
            async for chunk in self.chat_service.get_streaming_chat_message_content(
                chat_history=chat_history,
                settings=sk.connectors.ai.open_ai.OpenAIChatRequestSettings(
                    max_tokens=kwargs.get("max_tokens", 2000),
                    temperature=kwargs.get("temperature", 0.7)
                )
            ):
                if chunk.content:
                    yield str(chunk.content)
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Note: Anthropic support in SK may be limited, implementing basic version
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> str:
        """Get chat completion from Anthropic."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Convert messages
            formatted_messages = []
            for msg in messages:
                if msg.role in ["user", "assistant"]:
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            response = await client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                messages=formatted_messages
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Anthropic chat completion error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat completion from Anthropic."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Convert messages
            formatted_messages = []
            for msg in messages:
                if msg.role in ["user", "assistant"]:
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            async with client.messages.stream(
                model="claude-3-sonnet-20240229",
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                messages=formatted_messages
            ) as stream:
                async for chunk in stream.text_stream:
                    yield chunk
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise


class GoogleProvider(AIProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        
        # Fallback models in order of preference
        self.fallback_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "models/gemini-pro"  # Legacy model name as last resort
        ]
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> str:
        """Get chat completion from Google Gemini."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Try primary model first, then fallbacks
            models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
            
            last_error = None
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    
                    # Format conversation for Gemini
                    prompt = ""
                    for msg in messages:
                        if msg.role == "system":
                            prompt += f"System: {msg.content}\n\n"
                        elif msg.role == "user":
                            prompt += f"User: {msg.content}\n\n"
                        elif msg.role == "assistant":
                            prompt += f"Assistant: {msg.content}\n\n"
                    
                    response = await asyncio.to_thread(
                        model.generate_content,
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=kwargs.get("max_tokens", 2000),
                            temperature=kwargs.get("temperature", 0.7)
                        )
                    )
                    
                    logger.info(f"Successfully used Gemini model: {model_name}")
                    return response.text
                    
                except Exception as model_error:
                    logger.warning(f"Failed to use model {model_name}: {model_error}")
                    last_error = model_error
                    continue
            
            # If all models failed, raise the last error
            raise last_error or Exception("All Gemini models failed")
        
        except Exception as e:
            logger.error(f"Google Gemini chat completion error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat completion from Google Gemini."""
        # Note: Implement streaming if available in Gemini API
        response = await self.chat_completion(messages, **kwargs)
        yield response


class OllamaProvider(AIProvider):
    """Ollama local provider implementation."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> str:
        """Get chat completion from Ollama."""
        try:
            import httpx
            
            # Format messages for Ollama
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": kwargs.get("model", "llama2"),
                        "messages": formatted_messages,
                        "stream": False
                    }
                )
                response.raise_for_status()
                
                return response.json()["message"]["content"]
        
        except Exception as e:
            logger.error(f"Ollama chat completion error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat completion from Ollama."""
        try:
            import httpx
            import json
            
            # Format messages for Ollama
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": kwargs.get("model", "llama2"),
                        "messages": formatted_messages,
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
        
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise


class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI provider implementation."""
    
    def __init__(self, api_key: str, endpoint: str, deployment_name: str = "gpt-4"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> str:
        """Get chat completion from Azure OpenAI."""
        try:
            import openai
            
            # Configure Azure OpenAI client
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version="2024-02-15-preview"
            )
            
            # Format messages for OpenAI API
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.deployment_name,
                messages=formatted_messages,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI chat completion error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat completion from Azure OpenAI."""
        try:
            import openai
            
            # Configure Azure OpenAI client
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version="2024-02-15-preview"
            )
            
            # Format messages for OpenAI API
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.deployment_name,
                messages=formatted_messages,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Azure OpenAI streaming error: {e}")
            raise


class GenAIManager:
    """Manager for coordinating multiple AI providers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.providers: Dict[GenAIProvider, AIProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on configuration."""
        if self.settings.openai_api_key:            
            self.providers[GenAIProvider.OPENAI] = OpenAIProvider(self.settings.openai_api_key)
        
        if self.settings.anthropic_api_key:
            self.providers[GenAIProvider.ANTHROPIC] = AnthropicProvider(self.settings.anthropic_api_key)
        
        if self.settings.google_api_key:
            # Use gemini-1.5-flash as the default model
            google_model = getattr(self.settings, 'google_model', 'gemini-1.5-flash')
            self.providers[GenAIProvider.GOOGLE] = GoogleProvider(self.settings.google_api_key, google_model)
        
        if self.settings.azure_openai_key and self.settings.azure_openai_endpoint:
            # Azure OpenAI requires both API key and endpoint
            azure_deployment = getattr(self.settings, 'azure_deployment_name', 'gpt-4')
            self.providers[GenAIProvider.AZURE] = AzureOpenAIProvider(
                self.settings.azure_openai_key, 
                self.settings.azure_openai_endpoint,
                azure_deployment
            )
        
        if self.settings.ollama_base_url:
            self.providers[GenAIProvider.OLLAMA] = OllamaProvider(self.settings.ollama_base_url)
    
    def get_available_providers(self) -> List[GenAIProvider]:
        """Get list of available providers."""
        return list(self.providers.keys())
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        provider: Optional[GenAIProvider] = None,
        **kwargs
    ) -> str:
        """Get chat completion from specified or default provider."""
        provider = provider or self.settings.genai_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        return await self.providers[provider].chat_completion(messages, **kwargs)
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        provider: Optional[GenAIProvider] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion from specified or default provider."""
        provider = provider or self.settings.genai_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        async for chunk in self.providers[provider].stream_completion(messages, **kwargs):
            yield chunk