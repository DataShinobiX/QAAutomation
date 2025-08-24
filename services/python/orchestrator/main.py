"""
Smart Unified Test Orchestrator Service
FastAPI service that coordinates Figma + Document + LLM services for unified test generation
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from smart_unified_generator import SmartUnifiedTestGenerator

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Smart Unified Test Orchestrator Service")
    logger.info("Service URLs configured",
               figma_service="http://localhost:8001",
               document_service="http://localhost:8002",
               llm_service="http://localhost:8005")
    yield
    # Shutdown
    logger.info("Shutting down Smart Unified Test Orchestrator Service")

app = FastAPI(
    title="Smart Unified Test Orchestrator",
    description="AI-powered unified test generation combining Figma designs + requirements documents",
    version="1.0.0",
    lifespan=lifespan
)

# Service URLs
FIGMA_SERVICE_URL = "http://localhost:8001"
DOCUMENT_SERVICE_URL = "http://localhost:8002"
LLM_SERVICE_URL = "http://localhost:8005"

class RequirementsData(BaseModel):
    content: str
    file_type: str = "markdown"

class UnifiedTestRequest(BaseModel):
    figma_file_key: str
    target_url: str
    project_name: str = "Unified Test Project"
    requirements_document_path: Optional[str] = None
    requirements_data: Optional[RequirementsData] = None

class FileUploadRequest(BaseModel):
    figma_file_key: str
    target_url: str
    project_name: str = "Unified Test Project"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "smart-unified-test-orchestrator",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/generate-unified-tests")
async def generate_unified_tests(request: UnifiedTestRequest):
    """
    Generate unified test suite combining Figma design + requirements document
    """
    logger.info("Received unified test generation request",
               figma_file=request.figma_file_key,
               target_url=request.target_url,
               project_name=request.project_name,
               has_requirements_path=bool(request.requirements_document_path),
               has_requirements_data=bool(request.requirements_data))
    
    if not request.requirements_document_path and not request.requirements_data:
        raise HTTPException(
            status_code=400,
            detail="Either requirements_document_path or requirements_data is required for unified test generation"
        )
    
    try:
        # Handle inline requirements data
        requirements_path = request.requirements_document_path
        temp_file_path = None
        
        if request.requirements_data and not requirements_path:
            # Create temporary file for inline requirements
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix=f'.{request.requirements_data.file_type}',
                delete=False
            )
            temp_file.write(request.requirements_data.content)
            temp_file.close()
            temp_file_path = temp_file.name
            requirements_path = temp_file_path
            logger.info("Created temporary requirements file", path=requirements_path)
        
        async with SmartUnifiedTestGenerator(
            figma_service_url=FIGMA_SERVICE_URL,
            document_service_url=DOCUMENT_SERVICE_URL,
            llm_service_url=LLM_SERVICE_URL
        ) as generator:
            
            result = await generator.generate_smart_unified_tests(
                figma_file_key=request.figma_file_key,
                requirements_document_path=requirements_path,
                target_url=request.target_url,
                project_name=request.project_name
            )
            
            # Clean up temporary file
            if temp_file_path:
                os.unlink(temp_file_path)
                logger.info("Cleaned up temporary requirements file", path=temp_file_path)
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return JSONResponse(content=result)
            
    except Exception as e:
        logger.error("Unified test generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-unified-tests-upload")
async def generate_unified_tests_with_upload(
    figma_file_key: str = Form(...),
    target_url: str = Form(...),
    project_name: str = Form("Unified Test Project"),
    requirements_file: UploadFile = File(...)
):
    """
    Generate unified test suite with uploaded requirements document
    """
    logger.info("Received unified test generation request with file upload",
               figma_file=figma_file_key,
               target_url=target_url,
               project_name=project_name,
               filename=requirements_file.filename)
    
    # Save uploaded file temporarily
    import tempfile
    temp_file_path = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{requirements_file.filename}") as temp_file:
            content = await requirements_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Generate unified tests
        async with SmartUnifiedTestGenerator(
            figma_service_url=FIGMA_SERVICE_URL,
            document_service_url=DOCUMENT_SERVICE_URL,
            llm_service_url=LLM_SERVICE_URL
        ) as generator:
            
            result = await generator.generate_smart_unified_tests(
                figma_file_key=figma_file_key,
                requirements_document_path=temp_file_path,
                target_url=target_url,
                project_name=project_name
            )
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
            
            # Add file upload info to result
            result["upload_info"] = {
                "original_filename": requirements_file.filename,
                "file_size": requirements_file.size,
                "content_type": requirements_file.content_type
            }
            
            return JSONResponse(content=result)
            
    except Exception as e:
        logger.error("Unified test generation with upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.get("/service-status")
async def get_service_status():
    """
    Check status of all dependent services
    """
    logger.info("Checking dependent service status")
    
    import httpx
    services_status = {}
    
    services = {
        "figma_service": FIGMA_SERVICE_URL,
        "document_service": DOCUMENT_SERVICE_URL,
        "llm_service": LLM_SERVICE_URL
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        for service_name, service_url in services.items():
            try:
                response = await client.get(f"{service_url}/health")
                services_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url,
                    "response_time_ms": response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else None
                }
            except Exception as e:
                services_status[service_name] = {
                    "status": "unreachable",
                    "url": service_url,
                    "error": str(e)
                }
    
    all_healthy = all(status["status"] == "healthy" for status in services_status.values())
    
    return {
        "orchestrator_status": "healthy",
        "services": services_status,
        "all_services_healthy": all_healthy,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/capabilities")
async def get_capabilities():
    """
    Get orchestrator service capabilities
    """
    return {
        "service": "smart-unified-test-orchestrator",
        "version": "1.0.0",
        "capabilities": {
            "unified_test_generation": {
                "description": "Combines Figma design analysis with requirements documents for comprehensive test generation",
                "inputs": ["figma_file_key", "requirements_document", "target_url"],
                "outputs": ["unified_documented_tests", "ui_only_tests", "requirement_only_tests", "inferred_functionality_tests", "gap_analysis_tests"]
            },
            "ai_powered_mapping": {
                "description": "Uses AI to intelligently map UI components to business requirements",
                "features": ["smart_component_analysis", "requirement_extraction", "gap_detection", "inference_generation"]
            },
            "multi_service_coordination": {
                "description": "Coordinates multiple microservices for comprehensive test generation",
                "services": ["figma_integration", "document_parser", "llm_integration"]
            }
        },
        "supported_formats": {
            "figma_files": ["figma_file_key"],
            "document_formats": ["PDF", "Word", "Excel", "PowerPoint", "Markdown", "Text", "Notion", "Confluence"]
        },
        "test_categories": [
            {
                "name": "unified_documented_tests",
                "description": "Tests where UI elements are mapped to documented requirements"
            },
            {
                "name": "ui_only_tests", 
                "description": "Tests for UI elements not mentioned in documentation"
            },
            {
                "name": "requirement_only_tests",
                "description": "Tests for requirements without corresponding UI elements"
            },
            {
                "name": "inferred_functionality_tests",
                "description": "Tests for AI-inferred functionality based on UI and requirements"
            },
            {
                "name": "gap_analysis_tests",
                "description": "Tests identifying gaps between UI implementation and requirements"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8006))
    
    logger.info("Starting Smart Unified Test Orchestrator Service", port=port)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )