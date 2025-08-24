"""
Figma Integration Service
Extracts UI components, layouts, and design specifications from Figma files
"""
import asyncio
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import uvicorn

from config import FigmaServiceConfig
from models import BaseResponse, HealthResponse, ServiceStatus
from figma_client import FigmaClient
from figma_analyzer import FigmaAnalyzer
from test_generator import UITestGenerator

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global components
figma_client = None
figma_analyzer = None
test_generator = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global figma_client, figma_analyzer, test_generator, config
    
    # Startup
    logger.info("Starting Figma Integration Service")
    
    config = FigmaServiceConfig()
    figma_client = FigmaClient(config)
    figma_analyzer = FigmaAnalyzer(config)
    test_generator = UITestGenerator(config)
    
    # Test Figma connection
    try:
        await figma_client.test_connection()
        logger.info("Figma API connection successful")
    except Exception as e:
        logger.error("Failed to connect to Figma API", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Figma Integration Service")


app = FastAPI(
    title="Figma Integration Service",
    description="Extract UI components and generate tests from Figma designs",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    dependencies = {}
    
    # Check Figma API
    try:
        await figma_client.test_connection()
        dependencies["figma_api"] = ServiceStatus.HEALTHY
    except Exception:
        dependencies["figma_api"] = ServiceStatus.UNHEALTHY
    
    overall_status = ServiceStatus.HEALTHY
    if ServiceStatus.UNHEALTHY in dependencies.values():
        overall_status = ServiceStatus.UNHEALTHY
    elif ServiceStatus.DEGRADED in dependencies.values():
        overall_status = ServiceStatus.DEGRADED
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        uptime=0,  # TODO: implement uptime tracking
        dependencies=dependencies
    )


@app.get("/figma/file/{file_key}")
async def get_figma_file(file_key: str):
    """Get complete Figma file data"""
    try:
        logger.info("Fetching Figma file", file_key=file_key)
        file_data = await figma_client.get_file(file_key)
        
        return BaseResponse(
            success=True,
            message="Figma file retrieved successfully",
            service_name="figma-service"
        ), file_data
        
    except Exception as e:
        logger.error("Failed to fetch Figma file", file_key=file_key, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/figma/file/{file_key}/analyze")
async def analyze_figma_file(file_key: str):
    """Analyze Figma file and extract UI components"""
    try:
        logger.info("Analyzing Figma file", file_key=file_key)
        
        # Get file data
        file_data = await figma_client.get_file(file_key)
        
        # Analyze components
        analysis = await figma_analyzer.analyze_file(file_data)
        
        return {
            "success": True,
            "message": "Figma file analyzed successfully",
            "service_name": "figma-service",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error("Failed to analyze Figma file", file_key=file_key, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/figma/file/{file_key}/generate-tests")
async def generate_ui_tests(file_key: str, target_url: str):
    """Generate UI tests from Figma design"""
    try:
        logger.info("Generating UI tests", file_key=file_key, target_url=target_url)
        
        # Get and analyze file
        file_data = await figma_client.get_file(file_key)
        analysis = await figma_analyzer.analyze_file(file_data)
        
        # Generate tests
        test_suite = await test_generator.generate_ui_tests(analysis, target_url)
        
        return {
            "success": True,
            "message": "UI tests generated successfully",
            "service_name": "figma-service",
            "test_suite": test_suite
        }
        
    except Exception as e:
        logger.error("Failed to generate UI tests", file_key=file_key, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/figma/file/{file_key}/images")
async def get_figma_images(file_key: str, node_ids: str = None):
    """Get images/screenshots of Figma nodes"""
    try:
        node_id_list = node_ids.split(",") if node_ids else []
        
        images = await figma_client.get_images(file_key, node_id_list)
        
        return {
            "success": True,
            "message": "Figma images retrieved successfully",
            "service_name": "figma-service",
            "images": images
        }
        
    except Exception as e:
        logger.error("Failed to get Figma images", file_key=file_key, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/figma/compare-with-url")
async def compare_figma_with_website(
    file_key: str,
    target_url: str,
    frame_name: str = None
):
    """Compare Figma design with live website"""
    try:
        logger.info("Comparing Figma with website", 
                   file_key=file_key, target_url=target_url, frame_name=frame_name)
        
        # This will orchestrate with other services
        comparison = await figma_analyzer.compare_with_website(
            file_key, target_url, frame_name
        )
        
        return {
            "success": True,
            "message": "Comparison completed successfully",
            "service_name": "figma-service",
            "comparison": comparison
        }
        
    except Exception as e:
        logger.error("Failed to compare Figma with website", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/figma/styles/{file_key}")
async def get_figma_styles(file_key: str):
    """Get style guide from Figma file (colors, typography, etc.)"""
    try:
        logger.info("Extracting Figma styles", file_key=file_key)
        
        styles = await figma_analyzer.extract_styles(file_key)
        
        return {
            "success": True,
            "message": "Figma styles extracted successfully",
            "service_name": "figma-service",
            "styles": styles
        }
        
    except Exception as e:
        logger.error("Failed to extract Figma styles", file_key=file_key, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    config = FigmaServiceConfig()
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
        reload=config.debug
    )