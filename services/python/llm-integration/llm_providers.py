"""
LLM Provider Manager
Handles different LLM providers (Azure OpenAI, Anthropic, etc.)
"""
import asyncio
import os
import time
from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime

# Azure OpenAI
import openai
import tiktoken

# Anthropic Claude
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import LLMIntegrationConfig
from models import LLMRequest, LLMResponse, LLMProvider, ServiceStatus

logger = structlog.get_logger()


class LLMProviderError(Exception):
    """Custom exception for LLM provider errors"""
    pass


class AzureOpenAIProvider:
    """Azure OpenAI provider implementation"""
    
    def __init__(self, config: LLMIntegrationConfig):
        self.config = config
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Azure OpenAI client"""
        try:
            from openai import AzureOpenAI
            
            api_key = os.getenv("AZURE_OPENAI_API_KEY", 
                               "3bN0vkkmFI1bew2EXL1r0pNc7jxLv7XjZ3isd1tRduzxmiNYx0WlJQQJ99ALAC5RqLJXJ3w3AAABACOGUaC9")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", 
                                "https://opticustest.openai.azure.com/")
            
            self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
            
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version="2024-12-01-preview"
            )
            
            logger.info("Azure OpenAI client configured",
                       endpoint=endpoint,
                       deployment=self.deployment_name)
        except Exception as e:
            logger.error("Failed to setup Azure OpenAI client", error=str(e))
            raise LLMProviderError(f"Azure OpenAI setup failed: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test connection to Azure OpenAI"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10,
                temperature=0
            )
            return True
        except Exception as e:
            logger.error("Azure OpenAI connection test failed", error=str(e))
            return False
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Azure OpenAI"""
        start_time = time.time()
        
        try:
            messages = [{"role": "user", "content": request.prompt}]
            
            # Add context if provided
            if request.context:
                context_content = self._format_context(request.context)
                messages.insert(0, {"role": "system", "content": context_content})
            
            logger.info("Making Azure OpenAI request",
                       model=request.model,
                       max_tokens=request.max_tokens,
                       temperature=request.temperature)
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.deployment_name,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
            )
            
            processing_time = time.time() - start_time
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info("Azure OpenAI request completed",
                       tokens_used=tokens_used,
                       processing_time=processing_time)
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=request.model,
                tokens_used=tokens_used,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error("Azure OpenAI generation failed", error=str(e))
            raise LLMProviderError(f"Azure OpenAI generation failed: {str(e)}")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into system prompt"""
        context_parts = []
        
        if "role" in context:
            context_parts.append(f"Role: {context['role']}")
        
        if "task" in context:
            context_parts.append(f"Task: {context['task']}")
        
        if "constraints" in context:
            constraints = context["constraints"]
            if isinstance(constraints, list):
                context_parts.append(f"Constraints: {', '.join(constraints)}")
            else:
                context_parts.append(f"Constraints: {constraints}")
        
        if "format" in context:
            context_parts.append(f"Output format: {context['format']}")
        
        return "\n".join(context_parts)
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens for text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation
            return len(text.split()) * 1.3


class AnthropicProvider:
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: LLMIntegrationConfig):
        self.config = config
        self.client = None
        if ANTHROPIC_AVAILABLE:
            self._setup_client()
    
    def _setup_client(self):
        """Setup Anthropic client"""
        try:
            api_key = self.config.anthropic_api_key
            if not api_key:
                raise LLMProviderError("Anthropic API key not provided")
            
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic client configured")
        except Exception as e:
            logger.error("Failed to setup Anthropic client", error=str(e))
            raise LLMProviderError(f"Anthropic setup failed: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test connection to Anthropic"""
        if not ANTHROPIC_AVAILABLE or not self.client:
            return False
        
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error("Anthropic connection test failed", error=str(e))
            return False
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Anthropic Claude"""
        if not ANTHROPIC_AVAILABLE or not self.client:
            raise LLMProviderError("Anthropic not available")
        
        start_time = time.time()
        
        try:
            system_prompt = ""
            if request.context:
                system_prompt = self._format_context(request.context)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=request.model or "claude-3-sonnet-20240229",
                system=system_prompt,
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            processing_time = time.time() - start_time
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=request.model,
                tokens_used=tokens_used,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error("Anthropic generation failed", error=str(e))
            raise LLMProviderError(f"Anthropic generation failed: {str(e)}")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for Anthropic system prompt"""
        return self._format_context_common(context)


class LLMProviderManager:
    """Manager for all LLM providers"""
    
    def __init__(self, config: LLMIntegrationConfig):
        self.config = config
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        # Always add Azure OpenAI
        try:
            self.providers["azure_openai"] = AzureOpenAIProvider(self.config)
            logger.info("Azure OpenAI provider initialized")
        except Exception as e:
            logger.error("Failed to initialize Azure OpenAI provider", error=str(e))
        
        # Add Anthropic if available
        if ANTHROPIC_AVAILABLE and self.config.anthropic_api_key:
            try:
                self.providers["anthropic"] = AnthropicProvider(self.config)
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.error("Failed to initialize Anthropic provider", error=str(e))
    
    async def test_connections(self):
        """Test all provider connections"""
        for name, provider in self.providers.items():
            try:
                is_available = await provider.test_connection()
                logger.info("Provider connection test",
                           provider=name,
                           available=is_available)
            except Exception as e:
                logger.error("Provider connection test failed",
                           provider=name,
                           error=str(e))
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using specified provider"""
        provider_name = self._get_provider_name(request.provider)
        
        if provider_name not in self.providers:
            raise LLMProviderError(f"Provider {provider_name} not available")
        
        provider = self.providers[provider_name]
        return await provider.generate_text(request)
    
    def _get_provider_name(self, provider) -> str:
        """Map provider to internal provider names"""
        # Handle both string and enum inputs
        if isinstance(provider, str):
            if provider in ["azure_openai", "openai"]:
                return "azure_openai"
            elif provider == "anthropic":
                return "anthropic"
            else:
                return "azure_openai"  # Default to Azure OpenAI
        
        # Handle enum inputs
        mapping = {
            LLMProvider.OPENAI: "azure_openai",
            LLMProvider.AZURE_OPENAI: "azure_openai",
            LLMProvider.ANTHROPIC: "anthropic"
        }
        return mapping.get(provider, "azure_openai")
    
    async def get_provider_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all providers"""
        status = {}
        
        for name, provider in self.providers.items():
            try:
                is_available = await provider.test_connection()
                status[f"llm_provider_{name}"] = (
                    ServiceStatus.HEALTHY if is_available else ServiceStatus.UNHEALTHY
                )
            except Exception:
                status[f"llm_provider_{name}"] = ServiceStatus.UNHEALTHY
        
        return status
    
    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with their details"""
        providers_info = []
        
        for name, provider in self.providers.items():
            try:
                is_available = await provider.test_connection()
                
                provider_info = {
                    "name": name,
                    "display_name": name.replace("_", " ").title(),
                    "available": is_available,
                    "models": self._get_provider_models(name),
                    "capabilities": self._get_provider_capabilities(name)
                }
                
                providers_info.append(provider_info)
                
            except Exception as e:
                logger.error("Failed to get provider info", provider=name, error=str(e))
        
        return providers_info
    
    def _get_provider_models(self, provider_name: str) -> List[str]:
        """Get available models for provider"""
        models = {
            "azure_openai": ["gpt-4", "gpt-4-32k", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        }
        return models.get(provider_name, [])
    
    def _get_provider_capabilities(self, provider_name: str) -> List[str]:
        """Get capabilities for provider"""
        capabilities = {
            "azure_openai": ["text_generation", "code_generation", "analysis", "reasoning"],
            "anthropic": ["text_generation", "analysis", "reasoning", "long_context"]
        }
        return capabilities.get(provider_name, [])