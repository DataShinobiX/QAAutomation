"""
NLP Processing Service Configuration
"""
import os
from typing import Optional, List, Dict
from pydantic_settings import BaseSettings

class NLPConfig(BaseSettings):
    """NLP Processing Service Configuration"""
    
    # Service Configuration
    service_name: str = "nlp-processing"
    version: str = "1.0.0"
    port: int = int(os.getenv("PORT", 8003))
    host: str = "0.0.0.0"
    
    # NLP Model Configuration
    spacy_model: str = "en_core_web_sm"  # Default spaCy model
    spacy_models: List[str] = [
        "en_core_web_sm",    # English small
        "en_core_web_md",    # English medium
        "en_core_web_lg",    # English large
        "es_core_news_sm",   # Spanish small
        "fr_core_news_sm",   # French small
        "de_core_news_sm",   # German small
    ]
    
    # Transformer Models
    sentence_transformer_model: str = "all-MiniLM-L6-v2"  # Lightweight sentence embeddings
    ner_transformer_model: str = "dbmdz/bert-large-cased-finetuned-conll03-english"
    classification_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    
    # Text Processing Configuration
    max_text_length: int = 100000  # Maximum text length to process
    sentence_chunk_size: int = 512  # Chunk size for sentence processing
    similarity_threshold: float = 0.7  # Minimum similarity for text matching
    
    # Entity Recognition Configuration
    entity_types: List[str] = [
        "PERSON", "ORG", "GPE", "DATE", "TIME", "MONEY", 
        "PERCENT", "EMAIL", "URL", "PHONE", "PRODUCT", "EVENT"
    ]
    confidence_threshold: float = 0.8  # Minimum confidence for entity extraction
    
    # Language Detection Configuration
    supported_languages: List[str] = [
        "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ar", "hi", "ru"
    ]
    language_detection_confidence: float = 0.9
    
    # Text Analysis Configuration
    readability_metrics: List[str] = [
        "flesch_reading_ease", "flesch_kincaid_grade", "smog_index",
        "automated_readability_index", "coleman_liau_index", "gunning_fog"
    ]
    
    # Similarity and Clustering Configuration
    embedding_dimensions: int = 384  # Dimension of sentence embeddings
    clustering_min_samples: int = 2
    similarity_algorithms: List[str] = [
        "cosine", "jaccard", "levenshtein", "jaro_winkler", "semantic"
    ]
    
    # Text Classification Configuration
    classification_labels: List[str] = [
        "requirement", "user_story", "acceptance_criteria", "bug_report",
        "test_case", "feature_request", "technical_spec", "business_rule"
    ]
    
    # Keyword Extraction Configuration
    keyword_extraction_methods: List[str] = ["tfidf", "textrank", "yake", "keybert"]
    max_keywords: int = 20
    keyword_min_score: float = 0.1
    
    # Sentiment Analysis Configuration
    sentiment_models: List[str] = ["vader", "textblob", "transformer"]
    
    # Preprocessing Configuration
    preprocessing_options: Dict[str, bool] = {
        "lowercase": True,
        "remove_punctuation": False,
        "remove_stopwords": False,
        "lemmatization": True,
        "remove_extra_whitespace": True,
        "expand_contractions": True,
        "remove_urls": False,
        "remove_emails": False,
        "remove_phone_numbers": False,
    }
    
    # File Processing Configuration
    max_file_size_mb: int = 100  # Maximum file size for text processing
    supported_text_formats: List[str] = [
        "txt", "md", "csv", "json", "xml", "html", "rst"
    ]
    
    # Caching Configuration
    cache_embeddings: bool = True
    cache_ttl_hours: int = 24
    
    # Service Integration URLs
    document_parser_url: str = "http://localhost:8002"
    llm_integration_url: str = "http://localhost:8005"
    computer_vision_url: str = "http://localhost:8004"
    orchestrator_url: str = "http://localhost:8006"
    
    # Database Configuration
    redis_url: str = "redis://localhost:6379/3"  # Use database 3 for NLP service
    postgres_url: str = "postgresql://user:password@localhost:5432/qa_automation"
    
    # Model Storage Configuration
    model_cache_dir: str = os.path.join(os.getcwd(), "models")
    download_models_on_startup: bool = True
    
    # Performance Configuration
    batch_size: int = 32
    max_concurrent_requests: int = 10
    enable_gpu: bool = False  # Set to True if CUDA available
    
    # API Rate Limiting
    requests_per_minute: int = 1000
    max_tokens_per_request: int = 50000
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_model_performance: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global configuration instance
config = NLPConfig()