"""
NLP Processing Service - Minimal Version without Text Similarity
Advanced text analysis, entity extraction, and language processing
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from text_analyzer import TextAnalyzer, TextAnalysisResult
from entity_extractor import EntityExtractor, EntityExtractionResult

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.dev.set_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="NLP Processing Service", 
    description="Advanced text analysis, entity extraction, and language processing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for services
text_analyzer = None
entity_extractor = None

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str

class ServiceInfo(BaseModel):
    preprocessing_options: List[str]
    supported_languages: List[str]

class TextAnalysisRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"
    extract_keywords: bool = True
    extract_entities: bool = True
    analyze_sentiment: bool = True
    analyze_readability: bool = True
    extract_topics: bool = True
    include_linguistic_features: bool = True

class EntityExtractionRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"
    entity_types: Optional[List[str]] = None
    include_confidence: bool = True
    include_context: bool = True

@app.on_event("startup")
async def startup_event():
    """Initialize NLP services on startup"""
    global text_analyzer, entity_extractor
    
    logger.info("Starting NLP Processing Service",
                port=config.port,
                log_level=config.log_level)
    
    try:
        # Initialize text analyzer
        text_analyzer = TextAnalyzer()
        logger.info("Text Analyzer initialized successfully")
        
        # Initialize entity extractor
        entity_extractor = EntityExtractor()
        logger.info("Entity Extractor initialized successfully")
        
        logger.info("NLP Processing Service startup completed successfully")
        
    except Exception as e:
        logger.error("Failed to initialize NLP services", error=str(e))
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down NLP Processing Service")
    
    # Cleanup analyzers if needed
    if text_analyzer:
        # Any cleanup needed for text analyzer
        pass
    
    if entity_extractor:
        # Any cleanup needed for entity extractor
        pass

# Dependency to get text analyzer
def get_text_analyzer() -> TextAnalyzer:
    if text_analyzer is None:
        raise HTTPException(status_code=500, detail="Text analyzer not initialized")
    return text_analyzer

# Dependency to get entity extractor  
def get_entity_extractor() -> EntityExtractor:
    if entity_extractor is None:
        raise HTTPException(status_code=500, detail="Entity extractor not initialized")
    return entity_extractor

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="nlp-processing",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/info", response_model=ServiceInfo)  
async def get_service_info():
    """Get service information and capabilities"""
    return ServiceInfo(
        supported_languages=config.supported_languages,
        preprocessing_options=list(config.preprocessing_options.keys())
    )

@app.post("/analyze-text")
async def analyze_text(
    request: TextAnalysisRequest,
    analyzer: TextAnalyzer = Depends(get_text_analyzer)
) -> Dict[str, Any]:
    """Perform comprehensive text analysis"""
    
    try:
        if len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 50000:
            raise HTTPException(status_code=400, detail="Text too long (max: 50,000 characters)")
        
        result = await analyzer.analyze_text(
            text=request.text,
            language=request.language,
            extract_keywords=request.extract_keywords,
            extract_entities=request.extract_entities,
            analyze_sentiment=request.analyze_sentiment,
            analyze_readability=request.analyze_readability,
            extract_topics=request.extract_topics,
            include_linguistic_features=request.include_linguistic_features
        )
        
        response_data = {
            "text": result.text[:500] + "..." if len(result.text) > 500 else result.text,
            "language": result.language,
            "word_count": len(result.keywords) if hasattr(result, 'keywords') else 0,
            "entity_count": len(result.entities) if hasattr(result, 'entities') else 0,
            "analysis_metadata": result.analysis_metadata,
            "analyzed_at": result.analyzed_at.isoformat()
        }
        
        if request.extract_keywords and hasattr(result, 'keywords'):
            response_data["keywords"] = result.keywords[:20]  # Limit to top 20
        
        if request.extract_entities and hasattr(result, 'entities'):
            response_data["entities"] = result.entities[:50]  # Limit to top 50
            
        if request.analyze_sentiment and hasattr(result, 'sentiment'):
            response_data["sentiment"] = result.sentiment
            
        if request.analyze_readability and hasattr(result, 'readability'):
            response_data["readability"] = result.readability
            
        if request.extract_topics and hasattr(result, 'topics'):
            response_data["topics"] = result.topics[:10]  # Limit to top 10
            
        if request.include_linguistic_features and hasattr(result, 'linguistic_features'):
            response_data["linguistic_features"] = result.linguistic_features
        
        logger.info("Text analysis completed",
                   text_length=len(request.text),
                   language=result.language)
        
        return response_data
        
    except Exception as e:
        logger.error("Text analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@app.post("/extract-entities")
async def extract_entities(
    request: EntityExtractionRequest,
    extractor: EntityExtractor = Depends(get_entity_extractor)
) -> Dict[str, Any]:
    """Extract named entities from text"""
    
    try:
        if len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 50000:
            raise HTTPException(status_code=400, detail="Text too long (max: 50,000 characters)")
        
        result = await extractor.extract_entities(
            text=request.text,
            language=request.language,
            entity_types=request.entity_types,
            include_confidence=request.include_confidence,
            include_context=request.include_context
        )
        
        response_data = {
            "text": result.text[:500] + "..." if len(result.text) > 500 else result.text,
            "language": result.language,
            "entities": result.entities[:100],  # Limit to top 100
            "extraction_metadata": result.extraction_metadata,
            "extracted_at": result.extracted_at.isoformat()
        }
        
        logger.info("Entity extraction completed",
                   text_length=len(request.text),
                   entities_found=len(result.entities))
        
        return response_data
        
    except Exception as e:
        logger.error("Entity extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@app.get("/capabilities")
async def get_capabilities():
    """Get detailed service capabilities"""
    return {
        "service_name": "NLP Processing Service",
        "version": "1.0.0",
        "status": "operational",
        "components": {
            "text_analyzer_available": text_analyzer is not None,
            "entity_extractor_available": entity_extractor is not None,
            "spacy_models_loaded": (
                text_analyzer is not None and 
                hasattr(text_analyzer, 'nlp') and 
                text_analyzer.nlp is not None
            )
        },
        "features": {
            "text_analysis": True,
            "entity_extraction": True,
            "keyword_extraction": True,
            "sentiment_analysis": True,
            "readability_analysis": True,
            "topic_extraction": True,
            "linguistic_features": True,
            "multi_language_support": True
        },
        "model_info": {
            "spacy_models": ["en_core_web_sm", "en_core_web_md"],
            "supported_languages": config.supported_languages
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0", 
        port=8003,
        log_level="info",
        reload=False
    )