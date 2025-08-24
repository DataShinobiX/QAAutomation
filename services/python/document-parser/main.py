"""
Document Parser Service - Main FastAPI Application
Provides REST API for document parsing across multiple formats
"""
import asyncio
import os
import sys
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog
from datetime import datetime
import tempfile
import uuid

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from doc_parser_config import config
from parser_manager import DocumentParserManager
from llm_integration import DocumentToTestConverter

# Import models with fallback
try:
    from models import ParsedDocument, DocumentContent, ServiceStatus, HealthCheck
except ImportError:
    # Use models from parser_manager
    from parser_manager import ParsedDocument
    from document_parsers import DocumentContent
    from enum import Enum
    from pydantic import BaseModel
    from datetime import datetime
    
    class ServiceStatus(str, Enum):
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"
    
    class HealthCheck(BaseModel):
        service: str
        status: ServiceStatus
        timestamp: datetime
        version: str
        details: dict = {}

# Configure structured logging
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
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Document Parser Service",
    description="AI-powered document parsing service for QA automation",
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

# Initialize parser manager
parser_manager = DocumentParserManager()

# Ensure upload directory exists
os.makedirs(config.upload_dir, exist_ok=True)

# Store parsed documents temporarily (in production, use database)
parsed_documents_cache: Dict[str, ParsedDocument] = {}


# Request/Response Models
class ParseFileRequest(BaseModel):
    extract_images: bool = Field(default=False, description="Extract images from documents (PDF only)")
    include_metadata: bool = Field(default=True, description="Include document metadata")
    section_splitting: bool = Field(default=True, description="Split document into sections")


class ParseNotionRequest(BaseModel):
    page_id: str = Field(..., description="Notion page ID")
    include_children: bool = Field(default=False, description="Include child pages")


class ParseConfluenceRequest(BaseModel):
    page_id: str = Field(..., description="Confluence page ID")
    space_key: Optional[str] = Field(None, description="Confluence space key")


class BatchParseRequest(BaseModel):
    file_paths: List[str] = Field(..., description="List of file paths to parse")
    extract_images: bool = Field(default=False, description="Extract images from documents")
    max_concurrent: int = Field(default=5, description="Maximum concurrent parsing operations")


# LLM Integration Request Models
class DocumentToTestsRequest(BaseModel):
    document_id: Optional[str] = Field(None, description="ID of already parsed document")
    file_path: Optional[str] = Field(None, description="Path to document file")
    target_url: Optional[str] = Field(None, description="Target URL for testing")
    test_type: str = Field(default="functional", description="Type of tests to generate")
    include_edge_cases: bool = Field(default=True, description="Include edge case generation")
    include_test_data: bool = Field(default=True, description="Include test data generation")


class GenerateEdgeCasesRequest(BaseModel):
    document_id: Optional[str] = Field(None, description="ID of parsed document")
    file_path: Optional[str] = Field(None, description="Path to document file")
    existing_test_names: List[str] = Field(default_factory=list, description="Names of existing tests to avoid duplicating")


class GenerateTestDataRequest(BaseModel):
    document_id: str = Field(..., description="ID of parsed document")
    test_scenario_names: List[str] = Field(..., description="Names of test scenarios to generate data for")


class ParseResponse(BaseModel):
    success: bool
    document: Optional[ParsedDocument] = None
    error: Optional[str] = None
    processing_time: float


class BatchParseResponse(BaseModel):
    success: bool
    total_documents: int
    successful: int
    failed: int
    documents: List[ParsedDocument]
    processing_time: float


# Health Check
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        capabilities = await parser_manager.validate_parsing_capabilities()
        
        # Check upload directory
        upload_dir_accessible = os.path.exists(config.upload_dir) and os.access(config.upload_dir, os.W_OK)
        
        status = ServiceStatus.HEALTHY if upload_dir_accessible else ServiceStatus.DEGRADED
        
        return HealthCheck(
            service="document-parser",
            status=status,
            timestamp=datetime.now(),
            version="1.0.0",
            details={
                "upload_directory": config.upload_dir,
                "max_file_size": f"{config.max_file_size / (1024*1024):.1f}MB",
                "supported_formats": len(parser_manager.get_supported_formats()["local_files"]),
                "capabilities": capabilities
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthCheck(
            service="document-parser",
            status=ServiceStatus.UNHEALTHY,
            timestamp=datetime.now(),
            version="1.0.0",
            details={"error": str(e)}
        )


# File Upload and Parsing
@app.post("/parse/upload", response_model=ParseResponse)
async def parse_uploaded_file(
    file: UploadFile = File(...),
    extract_images: bool = False,
    include_metadata: bool = True,
    section_splitting: bool = True
):
    """Parse an uploaded file"""
    start_time = datetime.now()
    
    try:
        logger.info("File upload started", 
                   filename=file.filename, 
                   content_type=file.content_type)
        
        # Validate file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            supported_formats = parser_manager.get_supported_formats()["local_files"]
            
            if file_ext not in supported_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {file_ext}. Supported: {', '.join(supported_formats)}"
                )
        
        # Create temporary file
        temp_file_id = str(uuid.uuid4())
        temp_file_path = os.path.join(config.upload_dir, f"{temp_file_id}_{file.filename}")
        
        try:
            # Save uploaded file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info("File saved temporarily", temp_path=temp_file_path)
            
            # Parse the file
            parsed_doc = await parser_manager.parse_file(
                temp_file_path,
                extract_images=extract_images
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ParseResponse(
                success=parsed_doc.success,
                document=parsed_doc,
                error=parsed_doc.error_message if not parsed_doc.success else None,
                processing_time=processing_time
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info("Temporary file cleaned up", temp_path=temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File parsing failed", filename=file.filename, error=str(e))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=False,
            document=None,
            error=str(e),
            processing_time=processing_time
        )


# Local File Parsing
@app.post("/parse/file", response_model=ParseResponse)
async def parse_local_file(
    request: Optional[ParseFileRequest] = None,
    file_path: Optional[str] = None,
    extract_images: bool = False,
    include_metadata: bool = True,
    section_splitting: bool = True
):
    """Parse a local file by path"""
    start_time = datetime.now()
    
    # Handle both query parameter and request body
    if request and hasattr(request, 'file_path'):
        target_file_path = request.file_path
    elif file_path:
        target_file_path = file_path
    else:
        raise HTTPException(status_code=400, detail="file_path is required either as query parameter or in request body")
    
    try:
        logger.info("Local file parsing started", file_path=target_file_path)
        
        # Security check - ensure file is within allowed directory
        abs_file_path = os.path.abspath(target_file_path)
        
        # Parse the file
        parsed_doc = await parser_manager.parse_file(
            abs_file_path,
            extract_images=extract_images
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=parsed_doc.success,
            document=parsed_doc,
            error=parsed_doc.error_message if not parsed_doc.success else None,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Local file parsing failed", file_path=file_path, error=str(e))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=False,
            document=None,
            error=str(e),
            processing_time=processing_time
        )


# Batch File Parsing
@app.post("/parse/batch", response_model=BatchParseResponse)
async def parse_multiple_files(request: BatchParseRequest):
    """Parse multiple files concurrently"""
    start_time = datetime.now()
    
    try:
        logger.info("Batch parsing started", file_count=len(request.file_paths))
        
        # Limit concurrent operations
        if len(request.file_paths) > request.max_concurrent:
            file_batches = [
                request.file_paths[i:i + request.max_concurrent]
                for i in range(0, len(request.file_paths), request.max_concurrent)
            ]
        else:
            file_batches = [request.file_paths]
        
        all_results = []
        
        for batch in file_batches:
            batch_results = await parser_manager.parse_multiple_files(
                batch,
                extract_images=request.extract_images
            )
            all_results.extend(batch_results)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        successful = sum(1 for doc in all_results if doc.success)
        failed = len(all_results) - successful
        
        return BatchParseResponse(
            success=True,
            total_documents=len(all_results),
            successful=successful,
            failed=failed,
            documents=all_results,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Batch parsing failed", error=str(e))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return BatchParseResponse(
            success=False,
            total_documents=0,
            successful=0,
            failed=len(request.file_paths),
            documents=[],
            processing_time=processing_time
        )


# Notion Integration
@app.post("/parse/notion", response_model=ParseResponse)
async def parse_notion_page(request: ParseNotionRequest):
    """Parse a Notion page"""
    start_time = datetime.now()
    
    try:
        logger.info("Notion page parsing started", page_id=request.page_id)
        
        parsed_doc = await parser_manager.parse_notion_page(
            request.page_id,
            include_children=request.include_children
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=parsed_doc.success,
            document=parsed_doc,
            error=parsed_doc.error_message if not parsed_doc.success else None,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Notion parsing failed", page_id=request.page_id, error=str(e))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=False,
            document=None,
            error=str(e),
            processing_time=processing_time
        )


# Confluence Integration
@app.post("/parse/confluence", response_model=ParseResponse)
async def parse_confluence_page(request: ParseConfluenceRequest):
    """Parse a Confluence page"""
    start_time = datetime.now()
    
    try:
        logger.info("Confluence page parsing started", page_id=request.page_id)
        
        parsed_doc = await parser_manager.parse_confluence_page(
            request.page_id,
            space_key=request.space_key
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=parsed_doc.success,
            document=parsed_doc,
            error=parsed_doc.error_message if not parsed_doc.success else None,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Confluence parsing failed", page_id=request.page_id, error=str(e))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ParseResponse(
            success=False,
            document=None,
            error=str(e),
            processing_time=processing_time
        )


# Utility Endpoints
@app.get("/formats")
async def get_supported_formats():
    """Get list of supported document formats"""
    return parser_manager.get_supported_formats()


@app.get("/capabilities")
async def get_parsing_capabilities():
    """Get parsing capabilities and status"""
    return await parser_manager.validate_parsing_capabilities()


@app.get("/stats")
async def get_parsing_statistics():
    """Get parsing statistics and performance metrics"""
    return await parser_manager.get_parsing_statistics()


@app.post("/metadata")
async def extract_metadata_only(file_path: str):
    """Extract only metadata without full document parsing"""
    try:
        metadata = await parser_manager.extract_metadata_only(file_path)
        
        if metadata:
            return {"success": True, "metadata": metadata}
        else:
            return {"success": False, "error": "Could not extract metadata"}
            
    except Exception as e:
        logger.error("Metadata extraction failed", file_path=file_path, error=str(e))
        return {"success": False, "error": str(e)}


# LLM Integration Endpoints
@app.post("/generate/tests-from-document")
async def generate_tests_from_document(request: DocumentToTestsRequest):
    """Convert document to comprehensive test cases using LLM"""
    try:
        logger.info("Starting document to tests conversion", request=request.dict())
        
        # Get or parse the document
        parsed_doc = None
        
        if request.document_id and request.document_id in parsed_documents_cache:
            parsed_doc = parsed_documents_cache[request.document_id]
        elif request.file_path:
            # Parse the document first
            parse_result = await parser_manager.parse_file(request.file_path)
            if parse_result.success:
                parsed_doc = parse_result
                parsed_documents_cache[parse_result.id] = parse_result
            else:
                return {
                    "success": False,
                    "error": f"Document parsing failed: {parse_result.error_message}"
                }
        else:
            return {
                "success": False,
                "error": "Either document_id or file_path must be provided"
            }
        
        if not parsed_doc:
            return {
                "success": False,
                "error": "Document not found or could not be parsed"
            }
        
        # Convert document to tests using LLM
        async with DocumentToTestConverter() as converter:
            result = await converter.convert_requirements_to_tests(
                parsed_doc,
                target_url=request.target_url,
                test_type=request.test_type
            )
            
            # Generate edge cases if requested
            if request.include_edge_cases and result["success"]:
                edge_cases_result = await converter.generate_edge_cases_from_document(parsed_doc)
                if edge_cases_result["success"]:
                    result["edge_cases"] = edge_cases_result["edge_cases"]
            
            # Generate test data if requested
            if request.include_test_data and result["success"] and result["test_cases"]:
                test_scenarios = []
                for test_case in result["test_cases"]:
                    test_scenarios.extend(test_case.scenarios)
                
                test_data_result = await converter.generate_test_data_from_document(
                    parsed_doc, 
                    test_scenarios
                )
                if test_data_result["success"]:
                    result["test_data"] = test_data_result["test_data"]
        
        return result
        
    except Exception as e:
        logger.error("Document to tests conversion failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/generate/edge-cases")
async def generate_edge_cases(request: GenerateEdgeCasesRequest):
    """Generate edge cases from document content"""
    try:
        # Get or parse the document
        parsed_doc = None
        
        if request.document_id and request.document_id in parsed_documents_cache:
            parsed_doc = parsed_documents_cache[request.document_id]
        elif request.file_path:
            parse_result = await parser_manager.parse_file(request.file_path)
            if parse_result.success:
                parsed_doc = parse_result
                parsed_documents_cache[parse_result.id] = parse_result
            else:
                return {
                    "success": False,
                    "error": f"Document parsing failed: {parse_result.error_message}"
                }
        
        if not parsed_doc:
            return {
                "success": False,
                "error": "Document not found or could not be parsed"
            }
        
        # Generate edge cases
        async with DocumentToTestConverter() as converter:
            # Convert existing test names to TestScenario objects for compatibility
            existing_tests = []
            for test_name in request.existing_test_names:
                from llm_integration import TestScenario
                existing_tests.append(TestScenario(
                    name=test_name,
                    description="",
                    steps=[],
                    expected_outcome=""
                ))
            
            result = await converter.generate_edge_cases_from_document(
                parsed_doc,
                existing_tests
            )
        
        return result
        
    except Exception as e:
        logger.error("Edge case generation failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/generate/test-data")
async def generate_test_data(request: GenerateTestDataRequest):
    """Generate test data for specific scenarios"""
    try:
        if request.document_id not in parsed_documents_cache:
            return {
                "success": False,
                "error": "Document not found. Please parse the document first."
            }
        
        parsed_doc = parsed_documents_cache[request.document_id]
        
        # Create mock test scenarios from names
        from llm_integration import TestScenario
        test_scenarios = [
            TestScenario(
                name=name,
                description=f"Test scenario: {name}",
                steps=[],
                expected_outcome=""
            )
            for name in request.test_scenario_names
        ]
        
        # Generate test data
        async with DocumentToTestConverter() as converter:
            result = await converter.generate_test_data_from_document(
                parsed_doc,
                test_scenarios
            )
        
        return result
        
    except Exception as e:
        logger.error("Test data generation failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/parse-and-generate-tests")
async def parse_and_generate_tests(
    file: UploadFile = File(...),
    target_url: Optional[str] = None,
    test_type: str = "functional",
    include_edge_cases: bool = True,
    include_test_data: bool = True
):
    """One-step: Parse document and generate comprehensive test suite"""
    temp_file_path = None
    
    try:
        logger.info("Starting parse and generate tests workflow", 
                   filename=file.filename,
                   target_url=target_url)
        
        # Save uploaded file temporarily
        temp_file_id = str(uuid.uuid4())
        temp_file_path = os.path.join(config.upload_dir, f"{temp_file_id}_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse the document
        parsed_doc = await parser_manager.parse_file(temp_file_path)
        
        if not parsed_doc.success:
            return {
                "success": False,
                "error": f"Document parsing failed: {parsed_doc.error_message}",
                "parsing_result": None,
                "test_generation_result": None
            }
        
        # Store in cache for potential follow-up operations
        parsed_documents_cache[parsed_doc.id] = parsed_doc
        
        # Generate tests using LLM
        async with DocumentToTestConverter() as converter:
            test_result = await converter.convert_requirements_to_tests(
                parsed_doc,
                target_url=target_url,
                test_type=test_type
            )
            
            # Generate edge cases if requested
            if include_edge_cases and test_result["success"]:
                edge_cases_result = await converter.generate_edge_cases_from_document(parsed_doc)
                if edge_cases_result["success"]:
                    test_result["edge_cases"] = edge_cases_result["edge_cases"]
            
            # Generate test data if requested  
            if include_test_data and test_result["success"] and test_result.get("test_cases"):
                test_scenarios = []
                for test_case in test_result["test_cases"]:
                    if hasattr(test_case, 'scenarios'):
                        test_scenarios.extend(test_case.scenarios)
                
                if test_scenarios:
                    test_data_result = await converter.generate_test_data_from_document(
                        parsed_doc,
                        test_scenarios
                    )
                    if test_data_result["success"]:
                        test_result["test_data"] = test_data_result["test_data"]
        
        return {
            "success": True,
            "document_id": parsed_doc.id,
            "parsing_result": {
                "file_name": file.filename,
                "processing_time": parsed_doc.processing_time,
                "text_length": len(parsed_doc.content.text),
                "sections_count": len(parsed_doc.content.sections)
            },
            "test_generation_result": test_result
        }
        
    except Exception as e:
        logger.error("Parse and generate tests failed", 
                    filename=file.filename, 
                    error=str(e))
        return {
            "success": False,
            "error": str(e),
            "parsing_result": None,
            "test_generation_result": None
        }
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/documents/{document_id}")
async def get_parsed_document(document_id: str):
    """Get details of a parsed document"""
    if document_id not in parsed_documents_cache:
        raise HTTPException(status_code=404, detail="Document not found")
    
    parsed_doc = parsed_documents_cache[document_id]
    
    return {
        "document_id": parsed_doc.id,
        "source_type": parsed_doc.source_type,
        "source_path": parsed_doc.source_path,
        "parsed_at": parsed_doc.parsed_at,
        "processing_time": parsed_doc.processing_time,
        "success": parsed_doc.success,
        "metadata": {
            "file_name": parsed_doc.content.metadata.file_name if parsed_doc.content.metadata else "unknown",
            "file_size": parsed_doc.content.metadata.file_size if parsed_doc.content.metadata else 0,
            "document_type": parsed_doc.content.metadata.document_type if parsed_doc.content.metadata else "unknown",
            "sections_count": len(parsed_doc.content.sections),
            "text_length": len(parsed_doc.content.text)
        }
    }


@app.get("/documents")
async def list_parsed_documents():
    """List all parsed documents in cache"""
    documents = []
    
    for doc_id, parsed_doc in parsed_documents_cache.items():
        documents.append({
            "document_id": doc_id,
            "file_name": parsed_doc.content.metadata.file_name if parsed_doc.content.metadata else "unknown",
            "source_type": parsed_doc.source_type,
            "parsed_at": parsed_doc.parsed_at,
            "success": parsed_doc.success
        })
    
    return {
        "total_documents": len(documents),
        "documents": documents
    }


if __name__ == "__main__":
    logger.info("Starting Document Parser Service", 
               port=config.port, 
               upload_dir=config.upload_dir,
               max_file_size=f"{config.max_file_size / (1024*1024):.1f}MB")
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        access_log=True
    )