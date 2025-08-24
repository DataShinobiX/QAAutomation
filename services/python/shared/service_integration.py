"""
Service Integration Layer
Coordinates communication between Python AI services and Rust performance services
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

class ServiceEndpoint(BaseModel):
    """Configuration for a service endpoint"""
    name: str
    host: str = "localhost"
    port: int
    health_path: str = "/health"
    timeout: int = 30
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class ServiceStatus(BaseModel):
    """Status of a service"""
    name: str
    healthy: bool
    response_time_ms: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None

class IntegrationRequest(BaseModel):
    """Request for integrated service workflow"""
    url: str
    credentials: Optional[Dict[str, Any]] = None
    figma_file_key: Optional[str] = None
    requirements_data: Optional[Dict[str, Any]] = None
    workflow_type: str = Field(default="full_analysis")
    options: Dict[str, Any] = Field(default_factory=dict)

class IntegrationResult(BaseModel):
    """Result of integrated service workflow"""
    success: bool
    workflow_id: str
    execution_time: float
    results: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    service_statuses: Dict[str, bool] = Field(default_factory=dict)

class ServiceIntegrator:
    """Manages integration between all platform services"""
    
    def __init__(self):
        self.services = self._initialize_services()
        self.client = httpx.AsyncClient(timeout=30.0)
        self._service_cache = {}
        
    def _initialize_services(self) -> Dict[str, ServiceEndpoint]:
        """Initialize all service endpoints"""
        return {
            # Rust Performance Services
            "website_analyzer": ServiceEndpoint(name="website_analyzer", port=3001),
            "visual_engine": ServiceEndpoint(name="visual_engine", port=3002),
            "test_executor": ServiceEndpoint(name="test_executor", port=3003),
            
            # Python AI Services
            "figma_service": ServiceEndpoint(name="figma_service", port=8001),
            "document_parser": ServiceEndpoint(name="document_parser", port=8002),
            "nlp_service": ServiceEndpoint(name="nlp_service", port=8003),
            "computer_vision": ServiceEndpoint(name="computer_vision", port=8004),
            "llm_integration": ServiceEndpoint(name="llm_integration", port=8005),
            "orchestrator": ServiceEndpoint(name="orchestrator", port=8006),
            "auth_manager": ServiceEndpoint(name="auth_manager", port=8007),
        }
    
    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """Check health of a specific service"""
        service = self.services.get(service_name)
        if not service:
            return ServiceStatus(
                name=service_name,
                healthy=False,
                last_check=datetime.utcnow(),
                error_message="Service not configured"
            )
        
        start_time = datetime.utcnow()
        try:
            response = await self.client.get(
                f"{service.base_url}{service.health_path}",
                timeout=5.0
            )
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ServiceStatus(
                name=service_name,
                healthy=response.status_code == 200,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error_message=None if response.status_code == 200 else f"HTTP {response.status_code}"
            )
            
        except Exception as e:
            return ServiceStatus(
                name=service_name,
                healthy=False,
                response_time_ms=None,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def check_all_services_health(self) -> Dict[str, ServiceStatus]:
        """Check health of all services"""
        tasks = [
            self.check_service_health(service_name)
            for service_name in self.services.keys()
        ]
        
        statuses = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = {}
        for i, service_name in enumerate(self.services.keys()):
            if isinstance(statuses[i], Exception):
                result[service_name] = ServiceStatus(
                    name=service_name,
                    healthy=False,
                    last_check=datetime.utcnow(),
                    error_message=str(statuses[i])
                )
            else:
                result[service_name] = statuses[i]
        
        return result
    
    async def authenticate_if_needed(self, url: str, credentials: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Authenticate with website if credentials provided"""
        if not credentials:
            return None
        
        try:
            auth_service = self.services["auth_manager"]
            response = await self.client.post(
                f"{auth_service.base_url}/authenticate",
                json={
                    "url": url,
                    "username": credentials.get("username"),
                    "password": credentials.get("password"),
                    "auth_type": credentials.get("auth_type", "form_based"),
                    "additional_fields": credentials.get("additional_fields"),
                    "mfa_config": credentials.get("mfa_config"),
                    "timeout": credentials.get("timeout", 30),
                    "headless": credentials.get("headless", True)
                }
            )
            
            if response.status_code == 200:
                auth_result = response.json()
                if auth_result.get("success"):
                    return {
                        "cookies": auth_result.get("cookies", []),
                        "session_data": auth_result.get("session_data", {}),
                        "authenticated": True
                    }
            
            return {"authenticated": False, "error": "Authentication failed"}
            
        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            return {"authenticated": False, "error": str(e)}
    
    async def analyze_website(self, url: str, auth_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze website using Rust website analyzer"""
        try:
            analyzer_service = self.services["website_analyzer"]
            
            request_data = {"url": url}
            if auth_data and auth_data.get("cookies"):
                request_data["cookies"] = auth_data["cookies"]
            
            response = await self.client.post(
                f"{analyzer_service.base_url}/analyze",
                json=request_data
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Analysis failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def capture_screenshots(self, url: str, auth_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Capture screenshots using visual engine"""
        try:
            visual_service = self.services["visual_engine"]
            
            request_data = {
                "url": url,
                "wait_ms": 2000
            }
            if auth_data and auth_data.get("cookies"):
                request_data["cookies"] = auth_data["cookies"]
            
            response = await self.client.post(
                f"{visual_service.base_url}/capture",
                json=request_data
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Screenshot capture failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_figma_design(self, figma_file_key: str) -> Dict[str, Any]:
        """Parse Figma design using Figma service"""
        try:
            figma_service = self.services["figma_service"]
            
            response = await self.client.post(
                f"{figma_service.base_url}/analyze-figma-file",
                json={
                    "figma_file_key": figma_file_key,
                    "generate_tests": True
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Figma analysis failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_requirements(self, requirements_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse requirements using document parser"""
        try:
            parser_service = self.services["document_parser"]
            
            if "file_path" in requirements_data:
                response = await self.client.post(
                    f"{parser_service.base_url}/parse/file",
                    json={"file_path": requirements_data["file_path"]}
                )
            else:
                # Assume file content or URL parsing
                response = await self.client.post(
                    f"{parser_service.base_url}/parse/upload",
                    files={"file": requirements_data.get("file_content", "")}
                )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Requirements parsing failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_unified_tests(
        self, 
        figma_data: Optional[Dict[str, Any]] = None,
        requirements_data: Optional[Dict[str, Any]] = None,
        target_url: str = None
    ) -> Dict[str, Any]:
        """Generate unified tests using orchestrator"""
        try:
            orchestrator_service = self.services["orchestrator"]
            
            request_data = {}
            if figma_data:
                request_data["figma_analysis"] = figma_data
            if requirements_data:
                request_data["requirements_analysis"] = requirements_data
            if target_url:
                request_data["target_url"] = target_url
            
            response = await self.client.post(
                f"{orchestrator_service.base_url}/generate-unified-tests",
                json=request_data
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Test generation failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_tests(self, test_suite: Dict[str, Any], auth_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute tests using test executor"""
        try:
            executor_service = self.services["test_executor"]
            
            request_data = {"test_suite": test_suite}
            if auth_data and auth_data.get("cookies"):
                request_data["session_cookies"] = auth_data["cookies"]
            
            response = await self.client.post(
                f"{executor_service.base_url}/execute",
                json=request_data
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Test execution failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_integrated_workflow(self, request: IntegrationRequest) -> IntegrationResult:
        """Run complete integrated workflow"""
        start_time = datetime.utcnow()
        workflow_id = f"workflow_{int(start_time.timestamp())}"
        
        results = {}
        errors = []
        service_statuses = {}
        
        try:
            # 1. Check service health
            logger.info("Checking service health", workflow_id=workflow_id)
            health_status = await self.check_all_services_health()
            service_statuses = {name: status.healthy for name, status in health_status.items()}
            
            # Check if required services are healthy
            required_services = ["website_analyzer", "auth_manager"]
            if request.figma_file_key:
                required_services.append("figma_service")
            if request.requirements_data:
                required_services.extend(["document_parser", "orchestrator"])
            
            unhealthy_required = [svc for svc in required_services if not service_statuses.get(svc, False)]
            if unhealthy_required:
                errors.append(f"Required services unhealthy: {unhealthy_required}")
                return IntegrationResult(
                    success=False,
                    workflow_id=workflow_id,
                    execution_time=0,
                    results=results,
                    errors=errors,
                    service_statuses=service_statuses
                )
            
            # 2. Authentication if needed
            auth_data = None
            if request.credentials:
                logger.info("Authenticating with website", workflow_id=workflow_id)
                auth_data = await self.authenticate_if_needed(request.url, request.credentials)
                results["authentication"] = auth_data
                
                if not auth_data or not auth_data.get("authenticated"):
                    errors.append("Authentication failed")
            
            # 3. Website analysis
            logger.info("Analyzing website", workflow_id=workflow_id)
            analysis_result = await self.analyze_website(request.url, auth_data)
            results["website_analysis"] = analysis_result
            
            if not analysis_result.get("success"):
                errors.append(f"Website analysis failed: {analysis_result.get('error')}")
            
            # 4. Screenshots capture
            logger.info("Capturing screenshots", workflow_id=workflow_id)
            screenshots_result = await self.capture_screenshots(request.url, auth_data)
            results["screenshots"] = screenshots_result
            
            # 5. Figma analysis (if provided)
            figma_data = None
            if request.figma_file_key:
                logger.info("Analyzing Figma design", workflow_id=workflow_id)
                figma_result = await self.parse_figma_design(request.figma_file_key)
                results["figma_analysis"] = figma_result
                
                if figma_result.get("success"):
                    figma_data = figma_result.get("data")
                else:
                    errors.append(f"Figma analysis failed: {figma_result.get('error')}")
            
            # 6. Requirements parsing (if provided)
            requirements_parsed = None
            if request.requirements_data:
                logger.info("Parsing requirements", workflow_id=workflow_id)
                requirements_result = await self.parse_requirements(request.requirements_data)
                results["requirements_parsing"] = requirements_result
                
                if requirements_result.get("success"):
                    requirements_parsed = requirements_result.get("data")
                else:
                    errors.append(f"Requirements parsing failed: {requirements_result.get('error')}")
            
            # 7. Unified test generation (if we have figma or requirements)
            if figma_data or requirements_parsed:
                logger.info("Generating unified tests", workflow_id=workflow_id)
                tests_result = await self.generate_unified_tests(
                    figma_data=figma_data,
                    requirements_data=requirements_parsed,
                    target_url=request.url
                )
                results["unified_tests"] = tests_result
                
                # 8. Test execution (if tests were generated successfully)
                if tests_result.get("success") and request.workflow_type == "full_analysis":
                    logger.info("Executing tests", workflow_id=workflow_id)
                    test_suite = tests_result.get("data", {}).get("test_suite")
                    if test_suite:
                        execution_result = await self.execute_tests(test_suite, auth_data)
                        results["test_execution"] = execution_result
                        
                        if not execution_result.get("success"):
                            errors.append(f"Test execution failed: {execution_result.get('error')}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return IntegrationResult(
                success=len(errors) == 0,
                workflow_id=workflow_id,
                execution_time=execution_time,
                results=results,
                errors=errors,
                service_statuses=service_statuses
            )
            
        except Exception as e:
            logger.error("Integrated workflow failed", workflow_id=workflow_id, error=str(e))
            errors.append(f"Workflow execution failed: {str(e)}")
            
            return IntegrationResult(
                success=False,
                workflow_id=workflow_id,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                results=results,
                errors=errors,
                service_statuses=service_statuses
            )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global integrator instance
_integrator = None

def get_service_integrator() -> ServiceIntegrator:
    """Get or create the global service integrator"""
    global _integrator
    if _integrator is None:
        _integrator = ServiceIntegrator()
    return _integrator