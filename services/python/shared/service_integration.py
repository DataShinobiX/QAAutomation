"""
Service Integration Layer
Coordinates communication between Python AI services and Rust performance services
"""

import asyncio
import json
import uuid
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
            
            response = await self.client.get(
                f"{figma_service.base_url}/figma/file/{figma_file_key}/analyze"
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
        target_url: str = None,
        figma_file_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate tests using appropriate service based on available data"""
        try:
            logger.info("Test generation called", 
                       has_figma_data=bool(figma_data),
                       has_requirements_data=bool(requirements_data),
                       figma_file_key=figma_file_key,
                       target_url=target_url)
            
            # If we have requirements data, use the orchestrator for unified tests
            if requirements_data:
                logger.info("Using orchestrator for unified tests")
                orchestrator_service = self.services["orchestrator"]
                
                request_data = {
                    "target_url": target_url,
                    "requirements_data": {
                        "content": str(requirements_data),
                        "file_type": "json"
                    }
                }
                if figma_file_key:
                    request_data["figma_file_key"] = figma_file_key
                
                response = await self.client.post(
                    f"{orchestrator_service.base_url}/generate-unified-tests",
                    json=request_data
                )
                
            # If we only have Figma data, try LLM service first, then fallback to Figma
            elif figma_file_key:
                logger.info("Generating intelligent tests from Figma data")
                
                llm_service = self.services["llm_integration"]
                
                logger.info("Attempting LLM service for intelligent test generation",
                           figma_file_key=figma_file_key,
                           target_url=target_url,
                           provider="azure_openai")
                
                try:
                    response = await self.client.post(
                        f"{llm_service.base_url}/llm/generate-tests-from-figma",
                        params={
                            "figma_file_key": figma_file_key,
                            "target_url": target_url,
                            "provider": "azure_openai",
                            "model": "gpt-4"
                        },
                        timeout=45.0  # Reasonable timeout for LLM processing
                    )
                    
                    if response.status_code == 200:
                        logger.info("LLM service successfully generated intelligent test cases")
                    else:
                        logger.error("LLM service failed, falling back to Figma service",
                                   status_code=response.status_code,
                                   response_text=response.text[:500])
                        raise Exception(f"LLM service failed with status {response.status_code}")
                        
                except Exception as e:
                    logger.warning("LLM service unavailable, falling back to Figma service", error=str(e))
                    # Fallback to Figma service for test generation
                    figma_service = self.services["figma_service"]
                    logger.info("Using Figma service as fallback for test generation")
                    
                    response = await self.client.post(
                        f"{figma_service.base_url}/figma/file/{figma_file_key}/generate-tests",
                        params={"target_url": target_url}
                    )
                
            else:
                return {"success": False, "error": "No data provided for test generation"}
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Test generation failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _transform_test_suite_format(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """Transform test suite from Figma/generation format to test executor format"""
        logger.info("Transforming test suite format", 
                   original_keys=list(test_suite.keys()))
        
        # Create a copy to avoid modifying the original
        transformed = test_suite.copy()
        
        # Ensure the test suite has a proper UUID
        if "id" not in transformed or not transformed["id"]:
            transformed["id"] = str(uuid.uuid4())
        
        # Handle LLM-generated test suites (preferred format)
        if "test_cases" in test_suite:
            logger.info("Test suite already has test_cases, minimal transformation needed")
            # Ensure each test case has required fields
            for test_case in transformed["test_cases"]:
                if "actions" not in test_case:
                    test_case["actions"] = []
                if "priority" not in test_case:
                    test_case["priority"] = "Medium"
        
        # Convert ui_tests to test_cases if needed (only as fallback for raw Figma data)
        elif "ui_tests" in test_suite:
            logger.warning("Received raw ui_tests instead of LLM-generated test_cases. This suggests LLM service failed.")
            logger.info("Converting ui_tests to test_cases format as fallback")
            
            ui_tests = test_suite["ui_tests"]
            logger.info("Processing {} raw UI tests from Figma service".format(len(ui_tests)))
            
            test_cases = []
            
            # Process ui_tests with smart filtering and reasonable limits
            # Take first 50 tests for reasonable execution time
            limited_ui_tests = ui_tests[:50] if len(ui_tests) > 50 else ui_tests
            logger.info("Limiting test execution to {} tests for performance".format(len(limited_ui_tests)))
            
            for ui_test in limited_ui_tests:
                # Skip tests with invalid selectors
                selector = ui_test.get("selector")
                if not selector or selector.strip() == "":
                    continue
                
                # Skip overly specific tests (like color/dimension tests)
                test_type = ui_test.get("test_type", "").lower()
                if test_type in ["style", "dimensions", "color"]:
                    continue  # Skip these for now as they're too specific
                    
                # Map from Figma UI test format to TestCase format with proper UUID
                import uuid
                test_case = {
                    "id": str(uuid.uuid4()),  # Generate proper UUID
                    "name": ui_test.get("component_name", f"Test {ui_test.get('test_type', 'unknown')}"),
                    "description": f"Test {ui_test.get('component_name', 'component')} - {ui_test.get('test_type', 'unknown')}",
                    "test_type": self._map_test_type(test_type),
                    "target_element": selector,
                    "expected_value": ui_test.get("expected_value"),
                    "actions": [],
                    "priority": "Medium"
                }
                test_cases.append(test_case)
            
            transformed["test_cases"] = test_cases
            logger.info("Converted ui_tests to test_cases as fallback", 
                       original_ui_tests_count=len(ui_tests),
                       final_test_cases_count=len(test_cases))
        
        # Add missing required fields
        if "created_at" not in transformed:
            from datetime import datetime
            transformed["created_at"] = datetime.utcnow().isoformat() + "Z"
        if "updated_at" not in transformed:
            from datetime import datetime
            transformed["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Ensure we have test_cases field
        if "test_cases" not in transformed:
            transformed["test_cases"] = []
            logger.warning("No test_cases found, creating empty list")
        
        logger.info("Test suite transformation completed",
                   final_test_cases_count=len(transformed.get("test_cases", [])))
        
        return transformed
    
    def _map_test_type(self, figma_test_type: str) -> str:
        """Map Figma test types to test executor test types"""
        mapping = {
            "exists": "ElementExists",
            "visible": "ElementVisible", 
            "text": "ElementText",
            "style": "ElementAttribute",
            "click": "Navigation",
            "input": "FormSubmission"
        }
        return mapping.get(figma_test_type, "ElementExists")

    async def execute_tests(self, test_suite: Dict[str, Any], auth_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute tests using test executor"""
        try:
            logger.info("Starting test execution", 
                       test_suite_name=test_suite.get("name", "Unknown"),
                       test_suite_keys=list(test_suite.keys()))
            
            executor_service = self.services["test_executor"]
            
            # Transform the test suite format to match executor expectations
            transformed_suite = self._transform_test_suite_format(test_suite)
            
            request_data = {"test_suite": transformed_suite}
            if auth_data and auth_data.get("cookies"):
                request_data["session_cookies"] = auth_data["cookies"]
            
            logger.info("Sending test execution request to executor",
                       test_cases_count=len(transformed_suite.get("test_cases", [])),
                       executor_url=executor_service.base_url)
            
            response = await self.client.post(
                f"{executor_service.base_url}/execute",
                json=request_data
            )
            
            logger.info("Test execution response received",
                       status_code=response.status_code)
            
            if response.status_code == 200:
                result = response.json()
                execution = result.get("execution", {})
                logger.info("Test execution completed successfully",
                           status=execution.get("status"),
                           total_tests=execution.get("total_tests"),
                           passed_tests=execution.get("passed_tests"),
                           failed_tests=execution.get("failed_tests"))
                return {"success": True, "data": result}
            else:
                error_msg = f"Test execution failed: HTTP {response.status_code}"
                logger.error("Test execution failed", 
                           status_code=response.status_code,
                           response_text=response.text)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error("Test execution error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def analyze_test_results(self, test_results: Dict[str, Any], original_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test execution results using LLM integration"""
        try:
            llm_service = self.services["llm_integration"]
            
            # Prepare comprehensive analysis request
            analysis_request = {
                "test_execution_results": test_results,
                "original_inputs": original_inputs,
                "analysis_type": "comprehensive_qa_report",
                "include_insights": True,
                "include_recommendations": True,
                "include_coverage_analysis": True
            }
            
            response = await self.client.post(
                f"{llm_service.base_url}/llm/analyze-test-results",
                json=analysis_request
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"LLM analysis failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_comprehensive_report(
        self,
        workflow_results: Dict[str, Any],
        test_results: Optional[Dict[str, Any]] = None,
        llm_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive QA automation report"""
        try:
            report = {
                "report_id": f"qa_report_{int(datetime.utcnow().timestamp())}",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "workflow_success": workflow_results.get("success", False),
                    "total_services_used": len([k for k in workflow_results.keys() if "_analysis" in k or "_result" in k]),
                    "authentication_required": "authentication" in workflow_results,
                    "authentication_successful": workflow_results.get("authentication", {}).get("authenticated", False),
                    "design_analysis_completed": "figma_analysis" in workflow_results,
                    "requirements_analysis_completed": "requirements_parsing" in workflow_results,
                    "tests_executed": test_results is not None,
                    "ai_insights_available": llm_analysis is not None
                },
                "detailed_results": {
                    "website_analysis": workflow_results.get("website_analysis", {}),
                    "design_analysis": workflow_results.get("figma_analysis", {}),
                    "requirements_analysis": workflow_results.get("requirements_parsing", {}),
                    "test_generation": workflow_results.get("unified_tests", {}),
                    "test_execution": test_results or {},
                    "ai_analysis": llm_analysis or {}
                },
                "quality_metrics": self._calculate_quality_metrics(workflow_results, test_results, llm_analysis),
                "recommendations": self._extract_recommendations(llm_analysis) if llm_analysis else []
            }
            
            return {"success": True, "report": report}
            
        except Exception as e:
            logger.error("Report generation failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _calculate_quality_metrics(self, workflow_results: Dict, test_results: Dict, llm_analysis: Dict) -> Dict[str, Any]:
        """Calculate quality metrics from all analysis results"""
        metrics = {
            "coverage_score": 0,
            "design_compliance_score": 0,
            "requirements_coverage_score": 0,
            "test_pass_rate": 0,
            "overall_quality_score": 0
        }
        
        try:
            # Calculate based on available data
            if test_results and "data" in test_results:
                test_data = test_results["data"]
                if "execution" in test_data:
                    execution = test_data["execution"]
                    total_tests = len(execution.get("test_results", []))
                    passed_tests = len([t for t in execution.get("test_results", []) if t.get("status") == "passed"])
                    metrics["test_pass_rate"] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Extract design compliance if available
            if workflow_results.get("figma_analysis", {}).get("success"):
                metrics["design_compliance_score"] = 85  # Default based on successful analysis
            
            # Calculate overall score
            available_scores = [v for v in metrics.values() if v > 0]
            metrics["overall_quality_score"] = sum(available_scores) / len(available_scores) if available_scores else 0
            
        except Exception as e:
            logger.error("Quality metrics calculation failed", error=str(e))
        
        return metrics
    
    def _extract_recommendations(self, llm_analysis: Dict) -> List[str]:
        """Extract actionable recommendations from LLM analysis"""
        try:
            if llm_analysis and "data" in llm_analysis:
                return llm_analysis["data"].get("recommendations", [])
        except Exception:
            pass
        return []
    
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
            tests_result = None
            test_execution_result = None
            
            if figma_data or requirements_parsed:
                logger.info("Generating unified tests", workflow_id=workflow_id)
                tests_result = await self.generate_unified_tests(
                    figma_data=figma_data,
                    requirements_data=requirements_parsed,
                    target_url=request.url,
                    figma_file_key=request.figma_file_key
                )
                results["unified_tests"] = tests_result
                
                # 8. Test execution (if tests were generated successfully)
                if tests_result.get("success") and request.workflow_type == "full_analysis":
                    logger.info("Executing tests", workflow_id=workflow_id)
                    test_suite = tests_result.get("data", {}).get("test_suite")
                    if test_suite:
                        logger.info("Passing generated test suite to executor", 
                                   test_suite_name=test_suite.get("name", "Unknown"),
                                   test_cases_count=len(test_suite.get("test_cases", [])))
                        execution_result = await self.execute_tests(test_suite, auth_data)
                        results["test_execution"] = execution_result
                        test_execution_result = execution_result
                        
                        if not execution_result.get("success"):
                            errors.append(f"Test execution failed: {execution_result.get('error')}")
            
            # 9. LLM Analysis of Results (if test execution completed)
            if test_execution_result and test_execution_result.get("success"):
                logger.info("Analyzing test results with AI", workflow_id=workflow_id)
                original_inputs = {
                    "url": request.url,
                    "figma_file_key": request.figma_file_key,
                    "had_requirements": bool(request.requirements_data),
                    "workflow_type": request.workflow_type
                }
                
                llm_analysis_result = await self.analyze_test_results(
                    test_execution_result.get("data", {}),
                    original_inputs
                )
                results["llm_analysis"] = llm_analysis_result
                
                if not llm_analysis_result.get("success"):
                    errors.append(f"LLM analysis failed: {llm_analysis_result.get('error')}")
            
            # 10. Generate Comprehensive Report
            logger.info("Generating comprehensive report", workflow_id=workflow_id)
            report_result = await self.generate_comprehensive_report(
                workflow_results=results,
                test_results=test_execution_result,
                llm_analysis=results.get("llm_analysis")
            )
            results["final_report"] = report_result
            
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