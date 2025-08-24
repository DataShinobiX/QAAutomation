"""
Unified Workflow Orchestrator Service
Coordinates complete testing workflows using all platform services
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

import structlog
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../shared'))

from service_integration import (
    ServiceIntegrator, 
    IntegrationRequest, 
    IntegrationResult,
    get_service_integrator
)

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
    title="Unified Workflow Orchestrator",
    description="Orchestrates complete QA automation workflows across all platform services",
    version="1.0.0",
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

# Pydantic models
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "workflow-orchestrator"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class WorkflowRequest(BaseModel):
    url: str = Field(description="Target URL for testing")
    workflow_type: str = Field(default="full_analysis", description="Type of workflow to execute")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Authentication credentials")
    figma_file_key: Optional[str] = Field(None, description="Figma file key for design analysis")
    requirements_data: Optional[Dict[str, Any]] = Field(None, description="Requirements document data")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow options")

class WorkflowStatus(BaseModel):
    workflow_id: str
    status: str
    progress: float
    current_step: str
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)

# Global workflow tracking
active_workflows: Dict[str, WorkflowStatus] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Unified Workflow Orchestrator Service")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Unified Workflow Orchestrator Service")
    integrator = get_service_integrator()
    await integrator.close()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse()

@app.get("/service-status")
async def get_service_status():
    """Get status of all platform services"""
    integrator = get_service_integrator()
    
    try:
        health_status = await integrator.check_all_services_health()
        
        service_summary = {
            "total_services": len(health_status),
            "healthy_services": sum(1 for status in health_status.values() if status.healthy),
            "unhealthy_services": sum(1 for status in health_status.values() if not status.healthy),
            "last_check": datetime.utcnow().isoformat()
        }
        
        detailed_status = {}
        for name, status in health_status.items():
            detailed_status[name] = {
                "healthy": status.healthy,
                "response_time_ms": status.response_time_ms,
                "last_check": status.last_check.isoformat(),
                "error_message": status.error_message
            }
        
        return {
            "summary": service_summary,
            "services": detailed_status
        }
        
    except Exception as e:
        logger.error("Failed to get service status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check service status: {str(e)}")

@app.post("/workflows/start")
async def start_workflow(request: WorkflowRequest) -> Dict[str, Any]:
    """Start a new integrated workflow"""
    workflow_id = str(uuid.uuid4())
    
    logger.info("Starting workflow", 
                workflow_id=workflow_id, 
                url=request.url,
                workflow_type=request.workflow_type)
    
    # Initialize workflow status
    workflow_status = WorkflowStatus(
        workflow_id=workflow_id,
        status="initializing",
        progress=0.0,
        current_step="Validating request",
        start_time=datetime.utcnow()
    )
    active_workflows[workflow_id] = workflow_status
    
    try:
        # Create integration request
        integration_request = IntegrationRequest(
            url=request.url,
            credentials=request.credentials,
            figma_file_key=request.figma_file_key,
            requirements_data=request.requirements_data,
            workflow_type=request.workflow_type,
            options=request.options
        )
        
        # Start workflow in background
        asyncio.create_task(execute_workflow(workflow_id, integration_request))
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Workflow initiated successfully",
            "estimated_duration": "2-10 minutes",
            "monitoring_url": f"/workflows/{workflow_id}/status"
        }
        
    except Exception as e:
        logger.error("Failed to start workflow", workflow_id=workflow_id, error=str(e))
        workflow_status.status = "failed"
        workflow_status.current_step = f"Failed to start: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.post("/workflows/start-with-upload")
async def start_workflow_with_upload(
    url: str = Form(...),
    figma_file_key: Optional[str] = Form(None),
    workflow_type: str = Form("full_analysis"),
    requirements_file: Optional[UploadFile] = File(None),
    credentials_json: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Start workflow with file upload support"""
    import json
    
    workflow_id = str(uuid.uuid4())
    
    logger.info("Starting workflow with upload", 
                workflow_id=workflow_id,
                url=url,
                has_file=requirements_file is not None)
    
    try:
        # Parse credentials if provided
        credentials = None
        if credentials_json:
            credentials = json.loads(credentials_json)
        
        # Handle uploaded requirements file
        requirements_data = None
        if requirements_file:
            file_content = await requirements_file.read()
            requirements_data = {
                "file_content": file_content,
                "filename": requirements_file.filename,
                "content_type": requirements_file.content_type
            }
        
        # Create workflow request
        request = WorkflowRequest(
            url=url,
            workflow_type=workflow_type,
            credentials=credentials,
            figma_file_key=figma_file_key,
            requirements_data=requirements_data
        )
        
        return await start_workflow(request)
        
    except Exception as e:
        logger.error("Failed to start workflow with upload", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get status of a specific workflow"""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    status = active_workflows[workflow_id]
    return {
        "workflow_id": workflow_id,
        "status": status.status,
        "progress": status.progress,
        "current_step": status.current_step,
        "start_time": status.start_time.isoformat(),
        "estimated_completion": status.estimated_completion.isoformat() if status.estimated_completion else None,
        "results_available": len(status.results) > 0,
        "results_preview": {k: "available" for k in status.results.keys()}
    }

@app.get("/workflows/{workflow_id}/results")
async def get_workflow_results(workflow_id: str) -> Dict[str, Any]:
    """Get full results of a completed workflow"""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    status = active_workflows[workflow_id]
    
    if status.status not in ["completed", "failed"]:
        raise HTTPException(status_code=202, detail="Workflow still in progress")
    
    return {
        "workflow_id": workflow_id,
        "status": status.status,
        "execution_time": status.results.get("execution_time"),
        "results": status.results,
        "completed_at": datetime.utcnow().isoformat()
    }

@app.get("/workflows")
async def list_workflows() -> Dict[str, Any]:
    """List all workflows"""
    workflows_summary = []
    
    for workflow_id, status in active_workflows.items():
        workflows_summary.append({
            "workflow_id": workflow_id,
            "status": status.status,
            "progress": status.progress,
            "start_time": status.start_time.isoformat(),
            "current_step": status.current_step
        })
    
    return {
        "total_workflows": len(workflows_summary),
        "active_workflows": len([w for w in workflows_summary if w["status"] in ["initializing", "running"]]),
        "completed_workflows": len([w for w in workflows_summary if w["status"] == "completed"]),
        "workflows": workflows_summary
    }

@app.delete("/workflows/{workflow_id}")
async def cancel_workflow(workflow_id: str) -> Dict[str, Any]:
    """Cancel a running workflow"""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    status = active_workflows[workflow_id]
    
    if status.status in ["completed", "failed"]:
        # Just remove from active workflows
        del active_workflows[workflow_id]
        return {"message": "Workflow removed from active list"}
    else:
        # Cancel running workflow
        status.status = "cancelled"
        status.current_step = "Workflow cancelled by user"
        return {"message": "Workflow cancellation requested"}

async def execute_workflow(workflow_id: str, request: IntegrationRequest):
    """Execute the integrated workflow"""
    status = active_workflows[workflow_id]
    integrator = get_service_integrator()
    
    try:
        # Update status
        status.status = "running"
        status.current_step = "Checking service health"
        status.progress = 10.0
        
        # Execute integrated workflow
        result = await integrator.run_integrated_workflow(request)
        
        # Update progress during execution
        status.current_step = "Authentication"
        status.progress = 20.0
        await asyncio.sleep(0.1)  # Allow status updates
        
        status.current_step = "Website analysis"
        status.progress = 40.0
        await asyncio.sleep(0.1)
        
        status.current_step = "AI processing"
        status.progress = 70.0
        await asyncio.sleep(0.1)
        
        status.current_step = "Test generation"
        status.progress = 90.0
        await asyncio.sleep(0.1)
        
        # Store results
        status.results = {
            "success": result.success,
            "execution_time": result.execution_time,
            "workflow_results": result.results,
            "errors": result.errors,
            "service_statuses": result.service_statuses
        }
        
        # Final status
        if result.success:
            status.status = "completed"
            status.current_step = "Workflow completed successfully"
            status.progress = 100.0
        else:
            status.status = "failed" 
            status.current_step = f"Workflow failed: {'; '.join(result.errors)}"
            status.progress = 100.0
        
        logger.info("Workflow completed", 
                   workflow_id=workflow_id,
                   success=result.success,
                   execution_time=result.execution_time)
        
    except Exception as e:
        logger.error("Workflow execution failed", workflow_id=workflow_id, error=str(e))
        status.status = "failed"
        status.current_step = f"Execution failed: {str(e)}"
        status.progress = 100.0
        status.results = {"error": str(e)}

class QuickTestRequest(BaseModel):
    url: str = Field(..., description="URL of the website to test")
    credentials: Optional[Dict[str, Any]] = None

@app.post("/workflows/quick-test")
async def quick_test_workflow(
    request: QuickTestRequest  # Request body
) -> Dict[str, Any]:
    """Run a quick test workflow for immediate results"""
    
    logger.info("Starting quick test workflow", url=request.url, credentials_provided=request.credentials is not None)
    
    try:
        integrator = get_service_integrator()
        
        # Create simple integration request
        integration_request = IntegrationRequest(
            url=request.url,
            credentials=request.credentials,
            workflow_type="quick_analysis"
        )
        
        # Execute workflow
        result = await integrator.run_integrated_workflow(integration_request)
        
        return {
            "success": result.success,
            "execution_time": result.execution_time,
            "results": result.results,
            "errors": result.errors,
            "service_statuses": result.service_statuses
        }
        
    except Exception as e:
        logger.error("Quick test workflow failed", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Quick test failed: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Unified Workflow Orchestrator Service",
                host="0.0.0.0",
                port=8008)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )