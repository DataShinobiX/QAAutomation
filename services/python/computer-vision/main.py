"""
Computer Vision Service - Main FastAPI Application
Provides OCR, component detection, and accessibility analysis
"""
import asyncio
import os
import sys
import tempfile
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from ocr_processor import OCRProcessor, OCRResult
from component_detector import ComponentDetector, ComponentDetectionResult

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
    title="Computer Vision Service",
    description="OCR, component detection, and accessibility analysis for UI testing",
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
ocr_processor = None
component_detector = None

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = config.service_name
    version: str = config.version
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ServiceCapabilities(BaseModel):
    ocr_engines: List[str]
    supported_languages: List[str]
    supported_formats: List[str]
    component_types: List[str]
    accessibility_features: List[str]

class OCRRequest(BaseModel):
    image_path: Optional[str] = None
    language: str = "eng"
    preprocess: bool = True
    engine: str = "auto"

class OCRRegionRequest(BaseModel):
    image_path: str
    region: Dict[str, int] = Field(description="Dictionary with x, y, width, height")
    language: str = "eng"
    engine: str = "auto"

class ComponentDetectionRequest(BaseModel):
    image_path: str
    component_types: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None

class AccessibilityAnalysisRequest(BaseModel):
    image_path: str
    include_ocr: bool = True
    include_components: bool = True
    wcag_level: str = "AA"  # AA or AAA

class AccessibilityResult(BaseModel):
    image_path: str
    wcag_level: str
    issues: List[Dict[str, Any]]
    score: float
    recommendations: List[str]
    text_elements: List[Dict[str, Any]]
    components: List[Dict[str, Any]]
    analyzed_at: str

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global ocr_processor, component_detector
    
    logger.info("Starting Computer Vision Service", 
                version=config.version, 
                port=config.port)
    
    try:
        # Initialize OCR processor
        ocr_processor = OCRProcessor()
        logger.info("OCR Processor initialized successfully")
        
        # Initialize component detector
        component_detector = ComponentDetector()
        logger.info("Component Detector initialized successfully")
        
        # Create temp directory if it doesn't exist
        os.makedirs(config.temp_directory, exist_ok=True)
        
        logger.info("Computer Vision Service startup completed successfully")
        
    except Exception as e:
        logger.error("Failed to initialize Computer Vision Service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Computer Vision Service")

# Dependency to get OCR processor
def get_ocr_processor() -> OCRProcessor:
    if ocr_processor is None:
        raise HTTPException(status_code=500, detail="OCR processor not initialized")
    return ocr_processor

# Dependency to get component detector
def get_component_detector() -> ComponentDetector:
    if component_detector is None:
        raise HTTPException(status_code=500, detail="Component detector not initialized")
    return component_detector

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse()

@app.get("/capabilities", response_model=ServiceCapabilities)
async def get_capabilities():
    """Get service capabilities"""
    return ServiceCapabilities(
        ocr_engines=["tesseract", "easyocr", "auto"],
        supported_languages=config.ocr_languages,
        supported_formats=config.supported_image_formats,
        component_types=["button", "input", "text", "image", "icon", "checkbox", "dropdown"],
        accessibility_features=["contrast_analysis", "text_size_check", "color_analysis", "wcag_compliance"]
    )

@app.post("/ocr/extract-text")
async def extract_text_from_image(
    request: OCRRequest = None,
    image_file: UploadFile = File(None),
    language: str = Form("eng"),
    preprocess: bool = Form(True),
    engine: str = Form("auto"),
    ocr: OCRProcessor = Depends(get_ocr_processor)
) -> Dict[str, Any]:
    """Extract text from image using OCR"""
    
    try:
        # Handle file upload or path
        image_path = None
        temp_file_path = None
        
        if image_file:
            # Validate file type
            file_ext = image_file.filename.split('.')[-1].lower()
            if file_ext not in config.supported_image_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format: {file_ext}"
                )
            
            # Save uploaded file
            temp_file_path = os.path.join(
                config.temp_directory, 
                f"ocr_{uuid.uuid4()}.{file_ext}"
            )
            
            with open(temp_file_path, "wb") as buffer:
                content = await image_file.read()
                if len(content) > config.max_file_size_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size: {config.max_file_size_mb}MB"
                    )
                buffer.write(content)
            
            image_path = temp_file_path
            
        elif request and request.image_path:
            image_path = request.image_path
            if not os.path.exists(image_path):
                raise HTTPException(status_code=400, detail=f"Image file not found: {image_path}")
        else:
            raise HTTPException(status_code=400, detail="Either image_file or image_path must be provided")
        
        # Extract text
        result = await ocr.extract_text_from_image(
            image_path=image_path,
            language=language,
            preprocess=preprocess,
            engine=engine
        )
        
        # Convert OCRResult to dict
        response_data = {
            "text": result.text,
            "confidence": result.confidence,
            "bounding_boxes": result.bounding_boxes,
            "language": result.language,
            "engine": result.engine,
            "extracted_at": result.extracted_at.isoformat(),
            "character_count": len(result.text),
            "word_count": len(result.text.split()) if result.text else 0
        }
        
        logger.info("OCR text extraction completed",
                   confidence=result.confidence,
                   engine=result.engine,
                   text_length=len(result.text))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OCR text extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning("Failed to cleanup temp file", file=temp_file_path, error=str(e))

@app.post("/ocr/extract-region")
async def extract_text_from_region(
    request: OCRRegionRequest,
    ocr: OCRProcessor = Depends(get_ocr_processor)
) -> Dict[str, Any]:
    """Extract text from a specific region of an image"""
    
    try:
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=400, detail=f"Image file not found: {request.image_path}")
        
        result = await ocr.extract_text_from_region(
            image_path=request.image_path,
            region=request.region,
            language=request.language,
            engine=request.engine
        )
        
        response_data = {
            "text": result.text,
            "confidence": result.confidence,
            "bounding_boxes": result.bounding_boxes,
            "language": result.language,
            "engine": result.engine,
            "extracted_at": result.extracted_at.isoformat(),
            "region": request.region,
            "character_count": len(result.text),
            "word_count": len(result.text.split()) if result.text else 0
        }
        
        logger.info("OCR region extraction completed",
                   region=request.region,
                   confidence=result.confidence,
                   text_length=len(result.text))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OCR region extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Region OCR processing failed: {str(e)}")

@app.post("/ocr/batch-extract")
async def batch_extract_text(
    image_files: List[UploadFile] = File(...),
    language: str = Form("eng"),
    engine: str = Form("auto"),
    max_concurrent: int = Form(3),
    ocr: OCRProcessor = Depends(get_ocr_processor)
) -> Dict[str, Any]:
    """Extract text from multiple images concurrently"""
    
    if len(image_files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
    
    temp_files = []
    try:
        # Save all uploaded files
        image_paths = []
        for image_file in image_files:
            file_ext = image_file.filename.split('.')[-1].lower()
            if file_ext not in config.supported_image_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format in {image_file.filename}: {file_ext}"
                )
            
            temp_file_path = os.path.join(
                config.temp_directory, 
                f"batch_ocr_{uuid.uuid4()}.{file_ext}"
            )
            temp_files.append(temp_file_path)
            
            with open(temp_file_path, "wb") as buffer:
                content = await image_file.read()
                if len(content) > config.max_file_size_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large: {image_file.filename}. Maximum size: {config.max_file_size_mb}MB"
                    )
                buffer.write(content)
            
            image_paths.append(temp_file_path)
        
        # Process all images
        results = await ocr.batch_extract_text(
            image_paths=image_paths,
            language=language,
            engine=engine,
            max_concurrent=max_concurrent
        )
        
        # Convert results to response format
        response_results = []
        for i, result in enumerate(results):
            response_results.append({
                "filename": image_files[i].filename,
                "text": result.text,
                "confidence": result.confidence,
                "bounding_boxes": result.bounding_boxes,
                "language": result.language,
                "engine": result.engine,
                "extracted_at": result.extracted_at.isoformat(),
                "character_count": len(result.text),
                "word_count": len(result.text.split()) if result.text else 0
            })
        
        logger.info("Batch OCR extraction completed",
                   file_count=len(image_files),
                   successful=sum(1 for r in results if r.confidence > 0))
        
        return {
            "results": response_results,
            "total_files": len(image_files),
            "successful": sum(1 for r in results if r.confidence > 0),
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Batch OCR extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch OCR processing failed: {str(e)}")
    finally:
        # Cleanup temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file", file=temp_file, error=str(e))

@app.post("/components/detect")
async def detect_components(
    request: ComponentDetectionRequest = None,
    image_file: UploadFile = File(None),
    component_types: Optional[str] = Form(None),
    confidence_threshold: Optional[float] = Form(None),
    detector: ComponentDetector = Depends(get_component_detector)
) -> Dict[str, Any]:
    """Detect UI components in an image"""
    
    try:
        # Handle file upload or path
        image_path = None
        temp_file_path = None
        
        if image_file:
            file_ext = image_file.filename.split('.')[-1].lower()
            if file_ext not in config.supported_image_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format: {file_ext}"
                )
            
            temp_file_path = os.path.join(
                config.temp_directory, 
                f"component_{uuid.uuid4()}.{file_ext}"
            )
            
            with open(temp_file_path, "wb") as buffer:
                content = await image_file.read()
                if len(content) > config.max_file_size_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size: {config.max_file_size_mb}MB"
                    )
                buffer.write(content)
            
            image_path = temp_file_path
            
        elif request and request.image_path:
            image_path = request.image_path
            if not os.path.exists(image_path):
                raise HTTPException(status_code=400, detail=f"Image file not found: {image_path}")
        else:
            raise HTTPException(status_code=400, detail="Either image_file or image_path must be provided")
        
        # Parse component types if provided as string
        parsed_component_types = None
        if component_types:
            parsed_component_types = [t.strip() for t in component_types.split(",")]
        elif request and request.component_types:
            parsed_component_types = request.component_types
        
        # Use confidence threshold from request or form
        conf_threshold = confidence_threshold
        if conf_threshold is None and request:
            conf_threshold = request.confidence_threshold
        
        # Detect components
        result = await detector.detect_components(
            image_path=image_path,
            component_types=parsed_component_types,
            confidence_threshold=conf_threshold
        )
        
        # Convert result to response format
        components_data = []
        for comp in result.components:
            components_data.append({
                "component_type": comp.component_type,
                "confidence": comp.confidence,
                "bounding_box": comp.bounding_box,
                "properties": comp.properties,
                "center_point": comp.center_point
            })
        
        response_data = {
            "image_path": result.image_path,
            "components": components_data,
            "component_count": result.get_component_count(),
            "analysis_metadata": result.analysis_metadata,
            "detected_at": result.detected_at.isoformat(),
            "total_components": len(result.components)
        }
        
        logger.info("Component detection completed",
                   image_path=image_path,
                   components_found=len(result.components),
                   component_types=list(result.get_component_count().keys()))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Component detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Component detection failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning("Failed to cleanup temp file", file=temp_file_path, error=str(e))

@app.post("/accessibility/analyze", response_model=AccessibilityResult)
async def analyze_accessibility(
    request: AccessibilityAnalysisRequest = None,
    image_file: UploadFile = File(None),
    include_ocr: bool = Form(True),
    include_components: bool = Form(True),
    wcag_level: str = Form("AA"),
    ocr: OCRProcessor = Depends(get_ocr_processor),
    detector: ComponentDetector = Depends(get_component_detector)
) -> AccessibilityResult:
    """Analyze image for accessibility compliance"""
    
    try:
        # Handle file upload or path
        image_path = None
        temp_file_path = None
        
        if image_file:
            file_ext = image_file.filename.split('.')[-1].lower()
            if file_ext not in config.supported_image_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format: {file_ext}"
                )
            
            temp_file_path = os.path.join(
                config.temp_directory, 
                f"accessibility_{uuid.uuid4()}.{file_ext}"
            )
            
            with open(temp_file_path, "wb") as buffer:
                content = await image_file.read()
                buffer.write(content)
            
            image_path = temp_file_path
            
        elif request and request.image_path:
            image_path = request.image_path
            if not os.path.exists(image_path):
                raise HTTPException(status_code=400, detail=f"Image file not found: {image_path}")
        else:
            raise HTTPException(status_code=400, detail="Either image_file or image_path must be provided")
        
        # Use form parameters or request parameters
        if request:
            include_ocr = request.include_ocr
            include_components = request.include_components
            wcag_level = request.wcag_level
        
        issues = []
        recommendations = []
        text_elements = []
        components_data = []
        
        # OCR analysis for text accessibility
        if include_ocr:
            ocr_result = await ocr.extract_text_from_image(image_path)
            
            for bbox in ocr_result.bounding_boxes:
                text_element = {
                    "text": bbox["text"],
                    "bounding_box": {
                        "x": bbox["x"],
                        "y": bbox["y"],
                        "width": bbox["width"],
                        "height": bbox["height"]
                    },
                    "confidence": bbox["confidence"]
                }
                
                # Analyze text size (simplified - would need more sophisticated analysis)
                text_height = bbox["height"]
                estimated_font_size = text_height * 0.75  # Rough estimation
                
                if estimated_font_size < config.min_text_size_pt:
                    issues.append({
                        "type": "text_size",
                        "severity": "warning",
                        "message": f"Text may be too small: ~{estimated_font_size:.1f}pt (minimum {config.min_text_size_pt}pt)",
                        "element": text_element,
                        "wcag_guideline": "1.4.4 Resize text"
                    })
                
                text_elements.append(text_element)
        
        # Component analysis for UI accessibility
        if include_components:
            detection_result = await detector.detect_components(image_path)
            
            for comp in detection_result.components:
                component_data = {
                    "type": comp.component_type,
                    "confidence": comp.confidence,
                    "bounding_box": comp.bounding_box,
                    "center_point": comp.center_point
                }
                
                # Check component size for accessibility
                width = comp.bounding_box["width"]
                height = comp.bounding_box["height"]
                
                # Minimum touch target size (44x44 pt for mobile)
                if comp.component_type in ["button", "checkbox"] and (width < 44 or height < 44):
                    issues.append({
                        "type": "touch_target",
                        "severity": "warning",
                        "message": f"{comp.component_type} may be too small for touch: {width}x{height}px",
                        "element": component_data,
                        "wcag_guideline": "2.5.5 Target Size"
                    })
                
                components_data.append(component_data)
        
        # Calculate accessibility score (simplified)
        total_elements = len(text_elements) + len(components_data)
        critical_issues = len([i for i in issues if i["severity"] == "critical"])
        warning_issues = len([i for i in issues if i["severity"] == "warning"])
        
        if total_elements == 0:
            score = 1.0
        else:
            # Deduct points for issues
            score = max(0.0, 1.0 - (critical_issues * 0.2) - (warning_issues * 0.1))
        
        # Generate recommendations
        if critical_issues > 0:
            recommendations.append("Fix critical accessibility issues immediately")
        if warning_issues > 0:
            recommendations.append("Review and address accessibility warnings")
        if len(text_elements) == 0:
            recommendations.append("Consider adding alt text or text descriptions for images")
        
        recommendations.append(f"Ensure compliance with WCAG {wcag_level} guidelines")
        
        result = AccessibilityResult(
            image_path=image_path,
            wcag_level=wcag_level,
            issues=issues,
            score=score,
            recommendations=recommendations,
            text_elements=text_elements,
            components=components_data,
            analyzed_at=datetime.utcnow().isoformat()
        )
        
        logger.info("Accessibility analysis completed",
                   image_path=image_path,
                   score=score,
                   issues_found=len(issues),
                   text_elements=len(text_elements),
                   components=len(components_data))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Accessibility analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Accessibility analysis failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning("Failed to cleanup temp file", file=temp_file_path, error=str(e))

@app.get("/status")
async def get_service_status():
    """Get detailed service status"""
    
    status_info = {
        "service": config.service_name,
        "version": config.version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "ocr_available": ocr_processor is not None,
            "component_detection_available": component_detector is not None,
            "tesseract_available": ocr_processor._check_tesseract_available() if ocr_processor else False,
            "easyocr_available": bool(ocr_processor.easyocr_reader) if ocr_processor else False
        },
        "configuration": {
            "supported_formats": config.supported_image_formats,
            "max_file_size_mb": config.max_file_size_mb,
            "temp_directory": config.temp_directory,
            "ocr_confidence_threshold": config.ocr_confidence_threshold,
            "component_detection_confidence": config.component_detection_confidence
        }
    }
    
    return status_info

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Computer Vision Service",
                host=config.host,
                port=config.port)
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level=config.log_level.lower()
    )