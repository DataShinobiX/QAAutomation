"""
Shared configuration utilities for Python AI services
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class BaseServiceConfig(BaseSettings):
    """Base configuration for all Python services"""
    
    # Service info
    service_name: str = "ai-service"
    service_version: str = "0.1.0"
    debug: bool = False
    
    # API configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: Optional[str] = "postgresql://qa_user:qa_password@localhost:5433/qa_automation"
    
    # Redis for caching
    redis_url: Optional[str] = "redis://localhost:6380"
    
    # External services
    website_analyzer_url: str = "http://localhost:3001"
    visual_engine_url: str = "http://localhost:3002" 
    test_executor_url: str = "http://localhost:3003"
    
    # Figma configuration
    figma_token: Optional[str] = None
    figma_file_key: Optional[str] = None
    
    # LLM configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Document parsing
    notion_token: Optional[str] = None
    confluence_url: Optional[str] = None
    confluence_token: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        extra = "ignore"  # Ignore extra environment variables


class FigmaServiceConfig(BaseServiceConfig):
    """Figma service specific configuration"""
    service_name: str = "figma-service"
    port: int = 8001
    figma_token: str
    figma_file_key: str
    
    # Figma API settings
    figma_api_base_url: str = "https://api.figma.com/v1"
    cache_designs: bool = True
    cache_ttl: int = 3600  # 1 hour


class DocumentParserConfig(BaseServiceConfig):
    """Document parser service configuration"""
    service_name: str = "document-parser"
    port: int = 8002
    
    # File upload settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".pdf", ".docx", ".md"]
    upload_dir: str = "/tmp/uploads"


class NLPServiceConfig(BaseServiceConfig):
    """NLP service configuration"""
    service_name: str = "nlp-service"
    port: int = 8003
    
    # Model configuration
    spacy_model: str = "en_core_web_sm"
    transformers_model: str = "microsoft/DialoGPT-medium"
    device: str = "cpu"  # or "cuda" if GPU available


class ComputerVisionConfig(BaseServiceConfig):
    """Computer vision service configuration"""
    service_name: str = "computer-vision"
    port: int = 8004
    
    # CV settings
    detection_confidence: float = 0.7
    max_image_size: int = 2048
    supported_formats: list = ["png", "jpg", "jpeg", "webp"]


class LLMIntegrationConfig(BaseServiceConfig):
    """LLM integration service configuration"""
    service_name: str = "llm-integration"
    port: int = 8005
    
    # Default LLM settings - Use Azure OpenAI as default
    default_provider: str = "azure_openai"
    default_model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # Service URLs
    figma_service_url: str = "http://localhost:8001"
    
    # Azure OpenAI specific settings
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o"
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        extra = "ignore"  # Ignore extra environment variables


class OrchestratorConfig(BaseServiceConfig):
    """Orchestrator service configuration"""
    service_name: str = "orchestrator"
    port: int = 8006
    
    # Service discovery
    figma_service_url: str = "http://localhost:8001"
    document_parser_url: str = "http://localhost:8002"
    nlp_service_url: str = "http://localhost:8003"
    computer_vision_url: str = "http://localhost:8004"
    llm_integration_url: str = "http://localhost:8005"
    
    # Orchestration settings
    timeout: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay: int = 2