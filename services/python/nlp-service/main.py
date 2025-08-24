"""
NLP Processing Service - Main FastAPI Application
Advanced text analysis, entity extraction, and semantic processing
"""
import asyncio
import os
import sys
import tempfile
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import structlog
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from text_analyzer import TextAnalyzer, TextAnalysisResult
from entity_extractor import EntityExtractor, EntityExtractionResult
from text_similarity import TextSimilarityAnalyzer, SimilarityResult, TextClusterResult

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="NLP Processing Service",
    description="Advanced text analysis, entity extraction, and semantic processing for QA automation",
    version=config.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
text_analyzer = None
entity_extractor = None
similarity_analyzer = None

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = config.service_name
    version: str = config.version
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ServiceCapabilities(BaseModel):
    text_analysis_features: List[str]
    entity_types: List[str]
    similarity_algorithms: List[str]
    supported_languages: List[str]
    preprocessing_options: List[str]
    readability_metrics: List[str]

class TextAnalysisRequest(BaseModel):
    text: str = Field(description="Text to analyze")
    language: Optional[str] = None
    include_entities: bool = True
    include_sentiment: bool = True
    include_readability: bool = True
    include_keywords: bool = True
    include_linguistic_features: bool = True

class EntityExtractionRequest(BaseModel):
    text: str = Field(description="Text to extract entities from")
    entity_types: Optional[List[str]] = None
    include_custom: bool = True
    include_builtin: bool = True
    confidence_threshold: Optional[float] = None

class SimilarityRequest(BaseModel):
    text1: str = Field(description="First text for comparison")
    text2: str = Field(description="Second text for comparison")
    algorithms: Optional[List[str]] = None
    include_semantic: bool = True

class TextClusteringRequest(BaseModel):
    texts: List[str] = Field(description="List of texts to cluster")
    algorithm: str = "semantic"
    min_samples: int = 2
    eps: float = 0.3

class SimilarTextSearchRequest(BaseModel):
    query_text: str = Field(description="Query text to find similarities for")
    candidate_texts: List[str] = Field(description="Candidate texts to compare against")
    top_k: int = 5
    algorithm: str = "semantic"
    threshold: float = 0.5

class DuplicateDetectionRequest(BaseModel):
    texts: List[str] = Field(description="List of texts to check for duplicates")
    threshold: float = 0.9
    algorithm: str = "semantic"

class TextPreprocessingRequest(BaseModel):
    text: str = Field(description="Text to preprocess")
    options: Optional[Dict[str, bool]] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global text_analyzer, entity_extractor, similarity_analyzer
    
    logger.info("Starting NLP Processing Service",
                version=config.version,
                port=config.port)
    
    try:
        # Initialize text analyzer
        text_analyzer = TextAnalyzer()
        logger.info("Text Analyzer initialized successfully")
        
        # Initialize entity extractor
        entity_extractor = EntityExtractor()
        logger.info("Entity Extractor initialized successfully")
        
        # Initialize similarity analyzer
        similarity_analyzer = TextSimilarityAnalyzer()
        logger.info("Text Similarity Analyzer initialized successfully")
        
        # Create model cache directory
        os.makedirs(config.model_cache_dir, exist_ok=True)
        
        logger.info("NLP Processing Service startup completed successfully")
        
    except Exception as e:
        logger.error("Failed to initialize NLP Processing Service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down NLP Processing Service")

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

# Dependency to get similarity analyzer
def get_similarity_analyzer() -> TextSimilarityAnalyzer:
    if similarity_analyzer is None:
        raise HTTPException(status_code=500, detail="Similarity analyzer not initialized")
    return similarity_analyzer

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse()

@app.get("/capabilities", response_model=ServiceCapabilities)
async def get_capabilities():
    """Get service capabilities"""
    return ServiceCapabilities(
        text_analysis_features=[
            "sentiment_analysis", "readability_metrics", "keyword_extraction",
            "linguistic_features", "entity_extraction", "language_detection",
            "text_statistics", "pos_tagging", "dependency_parsing"
        ],
        entity_types=config.entity_types,
        similarity_algorithms=config.similarity_algorithms,
        supported_languages=config.supported_languages,
        preprocessing_options=list(config.preprocessing_options.keys()),
        readability_metrics=config.readability_metrics
    )

@app.post("/analyze/text")
async def analyze_text(
    request: TextAnalysisRequest = None,
    text_file: UploadFile = File(None),
    text: str = Form(None),
    language: Optional[str] = Form(None),
    include_entities: bool = Form(True),
    include_sentiment: bool = Form(True),
    include_readability: bool = Form(True),
    include_keywords: bool = Form(True),
    include_linguistic_features: bool = Form(True),
    analyzer: TextAnalyzer = Depends(get_text_analyzer)
) -> Dict[str, Any]:
    """Comprehensive text analysis"""
    
    try:
        # Determine text source
        input_text = None
        
        if text_file:
            # Handle file upload
            if text_file.size > config.max_file_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {config.max_file_size_mb}MB"
                )
            
            content = await text_file.read()
            input_text = content.decode('utf-8')
            
        elif text:
            input_text = text
        elif request and request.text:
            input_text = request.text
        else:
            raise HTTPException(status_code=400, detail="Text input required (text parameter, file upload, or JSON request)")
        
        # Use form parameters or request parameters
        if request:
            language = request.language or language
            include_entities = request.include_entities
            include_sentiment = request.include_sentiment
            include_readability = request.include_readability
            include_keywords = request.include_keywords
            include_linguistic_features = request.include_linguistic_features
        
        # Validate text length
        if len(input_text) > config.max_text_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long: {len(input_text)} characters (max: {config.max_text_length})"
            )
        
        # Perform analysis
        result = await analyzer.analyze_text(
            text=input_text,
            language=language,
            include_entities=include_entities,
            include_sentiment=include_sentiment,
            include_readability=include_readability,
            include_keywords=include_keywords,
            include_linguistic_features=include_linguistic_features
        )
        
        # Convert result to response format
        response_data = {
            "text": result.text,
            "language": result.language,
            "text_statistics": result.text_statistics,
            "readability_scores": result.readability_scores,
            "sentiment_scores": result.sentiment_scores,
            "keywords": result.keywords,
            "entities": result.entities,
            "linguistic_features": result.linguistic_features,
            "sentences": result.sentences,
            "tokens": result.tokens[:50],  # Limit tokens in response
            "analysis_metadata": result.analysis_metadata,
            "analyzed_at": result.analyzed_at.isoformat()
        }
        
        logger.info("Text analysis completed",
                   text_length=len(input_text),
                   language=result.language,
                   entities_found=len(result.entities),
                   keywords_found=len(result.keywords))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Text analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@app.post("/extract/entities")
async def extract_entities(
    request: EntityExtractionRequest = None,
    text_file: UploadFile = File(None),
    text: str = Form(None),
    entity_types: Optional[str] = Form(None),
    include_custom: bool = Form(True),
    include_builtin: bool = Form(True),
    confidence_threshold: Optional[float] = Form(None),
    extractor: EntityExtractor = Depends(get_entity_extractor)
) -> Dict[str, Any]:
    """Extract named entities from text"""
    
    try:
        # Determine text source
        input_text = None
        
        if text_file:
            content = await text_file.read()
            input_text = content.decode('utf-8')
        elif text:
            input_text = text
        elif request and request.text:
            input_text = request.text
        else:
            raise HTTPException(status_code=400, detail="Text input required")
        
        # Parse entity types if provided as string
        parsed_entity_types = None
        if entity_types:
            parsed_entity_types = [t.strip() for t in entity_types.split(",")]
        elif request and request.entity_types:
            parsed_entity_types = request.entity_types
        
        # Use form parameters or request parameters
        if request:
            include_custom = request.include_custom
            include_builtin = request.include_builtin
            confidence_threshold = request.confidence_threshold or confidence_threshold
        
        # Extract entities
        result = await extractor.extract_entities(
            text=input_text,
            include_custom=include_custom,
            include_builtin=include_builtin,
            confidence_threshold=confidence_threshold
        )
        
        # Filter by specific entity types if requested
        entities = result.entities
        if parsed_entity_types:
            entities = [e for e in entities if e["label"] in parsed_entity_types]
        
        response_data = {
            "text": result.text,
            "entities": entities,
            "entity_counts": result.get_entity_counts(),
            "extraction_metadata": result.extraction_metadata,
            "extracted_at": result.extracted_at.isoformat()
        }
        
        logger.info("Entity extraction completed",
                   text_length=len(input_text),
                   entities_found=len(entities),
                   entity_types=len(set(e["label"] for e in entities)))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Entity extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@app.post("/similarity/compare")
async def compare_text_similarity(
    request: SimilarityRequest,
    analyzer: TextSimilarityAnalyzer = Depends(get_similarity_analyzer)
) -> Dict[str, Any]:
    """Compare similarity between two texts"""
    
    try:
        result = await analyzer.compare_texts(
            text1=request.text1,
            text2=request.text2,
            algorithms=request.algorithms,
            include_semantic=request.include_semantic
        )
        
        response_data = {
            "text1": result.text1[:200] + "..." if len(result.text1) > 200 else result.text1,
            "text2": result.text2[:200] + "..." if len(result.text2) > 200 else result.text2,
            "similarity_scores": result.similarity_scores,
            "overall_similarity": result.get_overall_similarity(),
            "comparison_metadata": result.comparison_metadata,
            "compared_at": result.compared_at.isoformat()
        }
        
        logger.info("Text similarity comparison completed",
                   text1_length=len(request.text1),
                   text2_length=len(request.text2),
                   overall_similarity=result.get_overall_similarity())
        
        return response_data
        
    except Exception as e:
        logger.error("Text similarity comparison failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Similarity comparison failed: {str(e)}")

@app.post("/similarity/find-similar")
async def find_similar_texts(
    request: SimilarTextSearchRequest,
    analyzer: TextSimilarityAnalyzer = Depends(get_similarity_analyzer)
) -> Dict[str, Any]:
    """Find similar texts from a list of candidates"""
    
    try:
        if len(request.candidate_texts) > 1000:
            raise HTTPException(status_code=400, detail="Too many candidate texts (max: 1000)")
        
        similar_texts = await analyzer.find_similar_texts(
            query_text=request.query_text,
            candidate_texts=request.candidate_texts,
            top_k=request.top_k,
            algorithm=request.algorithm,
            threshold=request.threshold
        )
        
        response_data = {
            "query_text": request.query_text[:200] + "..." if len(request.query_text) > 200 else request.query_text,
            "candidates_searched": len(request.candidate_texts),
            "matches_found": len(similar_texts),
            "similar_texts": [
                {
                    "index": index,
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "similarity_score": score
                }
                for index, text, score in similar_texts
            ],
            "search_parameters": {
                "algorithm": request.algorithm,
                "threshold": request.threshold,
                "top_k": request.top_k
            }
        }
        
        logger.info("Similar text search completed",
                   query_length=len(request.query_text),
                   candidates_searched=len(request.candidate_texts),
                   matches_found=len(similar_texts))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Similar text search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Similar text search failed: {str(e)}")

@app.post("/similarity/cluster")
async def cluster_texts(
    request: TextClusteringRequest,
    analyzer: TextSimilarityAnalyzer = Depends(get_similarity_analyzer)
) -> Dict[str, Any]:
    """Cluster texts based on similarity"""
    
    try:
        if len(request.texts) > 500:
            raise HTTPException(status_code=400, detail="Too many texts for clustering (max: 500)")
        
        result = await analyzer.cluster_texts(
            texts=request.texts,
            algorithm=request.algorithm,
            min_samples=request.min_samples,
            eps=request.eps
        )
        
        cluster_summaries = result.get_cluster_summaries()
        
        response_data = {
            "total_texts": len(request.texts),
            "clusters": {
                str(cluster_id): {
                    "text_indices": indices,
                    "size": len(indices),
                    "sample_texts": [
                        request.texts[i][:100] + "..." if len(request.texts[i]) > 100 else request.texts[i]
                        for i in indices[:3]
                    ]
                }
                for cluster_id, indices in result.clusters.items()
            },
            "cluster_summaries": {
                str(k): v for k, v in cluster_summaries.items()
            },
            "cluster_metadata": result.cluster_metadata,
            "clustered_at": result.clustered_at.isoformat()
        }
        
        logger.info("Text clustering completed",
                   texts_clustered=len(request.texts),
                   clusters_found=result.cluster_metadata.get("total_clusters", 0))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Text clustering failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text clustering failed: {str(e)}")

@app.post("/similarity/detect-duplicates")
async def detect_duplicates(
    request: DuplicateDetectionRequest,
    analyzer: TextSimilarityAnalyzer = Depends(get_similarity_analyzer)
) -> Dict[str, Any]:
    """Detect duplicate or near-duplicate texts"""
    
    try:
        if len(request.texts) > 200:
            raise HTTPException(status_code=400, detail="Too many texts for duplicate detection (max: 200)")
        
        duplicates = await analyzer.detect_duplicates(
            texts=request.texts,
            threshold=request.threshold,
            algorithm=request.algorithm
        )
        
        response_data = {
            "total_texts": len(request.texts),
            "duplicates_found": len(duplicates),
            "duplicates": [
                {
                    "index1": index1,
                    "index2": index2,
                    "text1": request.texts[index1][:100] + "..." if len(request.texts[index1]) > 100 else request.texts[index1],
                    "text2": request.texts[index2][:100] + "..." if len(request.texts[index2]) > 100 else request.texts[index2],
                    "similarity_score": score
                }
                for index1, index2, score in duplicates
            ],
            "detection_parameters": {
                "algorithm": request.algorithm,
                "threshold": request.threshold
            }
        }
        
        logger.info("Duplicate detection completed",
                   texts_analyzed=len(request.texts),
                   duplicates_found=len(duplicates))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Duplicate detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Duplicate detection failed: {str(e)}")

@app.post("/preprocess/text")
async def preprocess_text(
    request: TextPreprocessingRequest = None,
    text: str = Form(None),
    options: Optional[str] = Form(None),
    analyzer: TextAnalyzer = Depends(get_text_analyzer)
) -> Dict[str, Any]:
    """Preprocess text according to specified options"""
    
    try:
        # Determine text source
        input_text = text or (request.text if request else None)
        if not input_text:
            raise HTTPException(status_code=400, detail="Text input required")
        
        # Parse preprocessing options
        preprocessing_options = None
        if options:
            # Expect comma-separated key=value pairs
            try:
                option_pairs = [opt.strip().split('=') for opt in options.split(',')]
                preprocessing_options = {key: value.lower() == 'true' for key, value in option_pairs}
            except:
                raise HTTPException(status_code=400, detail="Invalid options format. Use: key1=true,key2=false")
        elif request and request.options:
            preprocessing_options = request.options
        
        # Preprocess text
        processed_text = await analyzer.preprocess_text(
            text=input_text,
            options=preprocessing_options
        )
        
        response_data = {
            "original_text": input_text,
            "processed_text": processed_text,
            "original_length": len(input_text),
            "processed_length": len(processed_text),
            "preprocessing_options": preprocessing_options or config.preprocessing_options,
            "reduction_ratio": round(1 - (len(processed_text) / len(input_text)), 3) if len(input_text) > 0 else 0
        }
        
        logger.info("Text preprocessing completed",
                   original_length=len(input_text),
                   processed_length=len(processed_text))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Text preprocessing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text preprocessing failed: {str(e)}")

@app.get("/analyze/language")
async def detect_language(
    text: str = Query(..., description="Text to detect language for"),
    analyzer: TextAnalyzer = Depends(get_text_analyzer)
) -> Dict[str, Any]:
    """Detect the language of given text"""
    
    try:
        # Use the analyzer's language detection method
        language = await analyzer._detect_language(text)
        
        # Get additional language information
        from langdetect import detect_probs
        
        try:
            probabilities = detect_probs(text[:1000])  # Use first 1000 chars
            language_probs = [
                {"language": prob.lang, "probability": round(prob.prob, 3)}
                for prob in probabilities[:5]  # Top 5 languages
            ]
        except:
            language_probs = [{"language": language, "probability": 1.0}]
        
        response_data = {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "detected_language": language,
            "language_probabilities": language_probs,
            "supported_languages": config.supported_languages,
            "text_length": len(text)
        }
        
        logger.info("Language detection completed",
                   text_length=len(text),
                   detected_language=language)
        
        return response_data
        
    except Exception as e:
        logger.error("Language detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")

@app.get("/status")
async def get_service_status():
    """Get detailed service status"""
    
    status_info = {
        "service": config.service_name,
        "version": config.version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "text_analyzer_available": text_analyzer is not None,
            "entity_extractor_available": entity_extractor is not None,
            "similarity_analyzer_available": similarity_analyzer is not None,
            "semantic_similarity_available": (
                similarity_analyzer is not None and 
                similarity_analyzer.sentence_model is not None
            ),
            "spacy_models_loaded": (
                len(text_analyzer.nlp_models) if text_analyzer else 0
            )
        },
        "configuration": {
            "max_text_length": config.max_text_length,
            "supported_languages": config.supported_languages,
            "entity_types": config.entity_types,
            "similarity_algorithms": config.similarity_algorithms
        },
        "model_info": {
            "sentence_transformer": config.sentence_transformer_model,
            "spacy_models": config.spacy_models,
            "model_cache_dir": config.model_cache_dir
        }
    }
    
    return status_info

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting NLP Processing Service",
                host=config.host,
                port=config.port)
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level=config.log_level.lower()
    )