"""
LLM Integration Service
Provides intelligent test generation and optimization using Azure OpenAI and other LLM providers
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

from config import LLMIntegrationConfig
from models import BaseResponse, HealthResponse, ServiceStatus, LLMRequest, LLMResponse
from llm_providers import LLMProviderManager
from test_generator import IntelligentTestGenerator
from prompt_manager import PromptManager
from rate_limiter import RateLimiter

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
llm_manager = None
test_generator = None
prompt_manager = None
rate_limiter = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global llm_manager, test_generator, prompt_manager, rate_limiter, config
    
    # Startup
    logger.info("Starting LLM Integration Service")
    
    config = LLMIntegrationConfig()
    llm_manager = LLMProviderManager(config)
    test_generator = IntelligentTestGenerator(config, llm_manager)
    prompt_manager = PromptManager()
    rate_limiter = RateLimiter(config)
    
    # Test LLM connection
    try:
        await llm_manager.test_connections()
        logger.info("LLM providers initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize LLM providers", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down LLM Integration Service")


app = FastAPI(
    title="LLM Integration Service",
    description="Intelligent test generation and optimization using AI",
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
    
    # Check LLM providers
    provider_status = await llm_manager.get_provider_status()
    dependencies.update(provider_status)
    
    # Service is healthy if at least one provider is healthy
    healthy_providers = [status for status in dependencies.values() if status == ServiceStatus.HEALTHY]
    
    if len(healthy_providers) > 0:
        overall_status = ServiceStatus.HEALTHY
        if ServiceStatus.DEGRADED in dependencies.values():
            overall_status = ServiceStatus.DEGRADED
    else:
        overall_status = ServiceStatus.UNHEALTHY
    
    return HealthResponse(
        success=overall_status == ServiceStatus.HEALTHY,
        message=f"LLM Integration Service is {overall_status.value}",
        status=overall_status,
        version="0.1.0",
        uptime=0,  # TODO: implement uptime tracking
        dependencies=dependencies
    )


@app.post("/llm/generate")
async def generate_text(request: LLMRequest):
    """Generate text using specified LLM provider"""
    try:
        # Check rate limits
        if not await rate_limiter.check_rate_limit("generate", request.provider):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        logger.info("Generating text", 
                   provider=request.provider, 
                   model=request.model,
                   prompt_length=len(request.prompt))
        
        response = await llm_manager.generate_text(request)
        
        logger.info("Text generation completed",
                   provider=request.provider,
                   tokens_used=response.tokens_used,
                   processing_time=response.processing_time)
        
        return {
            "success": True,
            "message": "Text generated successfully",
            "service_name": "llm-integration",
            "response": response
        }
        
    except Exception as e:
        logger.error("Text generation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/generate-tests-from-figma")
async def generate_tests_from_figma(
    figma_file_key: str,
    target_url: str,
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Generate intelligent tests from Figma design analysis"""
    try:
        logger.info("Generating tests from Figma design",
                   figma_file_key=figma_file_key,
                   target_url=target_url,
                   provider=provider)
        
        test_suite = await test_generator.generate_from_figma(
            figma_file_key=figma_file_key,
            target_url=target_url,
            provider=provider,
            model=model
        )
        
        return {
            "success": True,
            "message": "Tests generated from Figma design successfully",
            "service_name": "llm-integration",
            "test_suite": test_suite
        }
        
    except Exception as e:
        logger.error("Failed to generate tests from Figma", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/generate-tests-from-requirements")
async def generate_tests_from_requirements(
    requirements_text: str,
    target_url: str,
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Generate tests from requirements/user stories"""
    try:
        logger.info("Generating tests from requirements",
                   target_url=target_url,
                   requirements_length=len(requirements_text),
                   provider=provider)
        
        test_suite = await test_generator.generate_from_requirements(
            requirements_text=requirements_text,
            target_url=target_url,
            provider=provider,
            model=model
        )
        
        return {
            "success": True,
            "message": "Tests generated from requirements successfully",
            "service_name": "llm-integration",
            "test_suite": test_suite
        }
        
    except Exception as e:
        logger.error("Failed to generate tests from requirements", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/optimize-test-suite")
async def optimize_test_suite(
    test_suite_data: dict,
    optimization_goals: list = ["coverage", "efficiency", "maintainability"],
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Optimize existing test suite using AI"""
    try:
        logger.info("Optimizing test suite",
                   test_count=len(test_suite_data.get("ui_tests", [])),
                   goals=optimization_goals,
                   provider=provider)
        
        optimized_suite = await test_generator.optimize_test_suite(
            test_suite_data=test_suite_data,
            optimization_goals=optimization_goals,
            provider=provider,
            model=model
        )
        
        return {
            "success": True,
            "message": "Test suite optimized successfully",
            "service_name": "llm-integration",
            "optimized_suite": optimized_suite
        }
        
    except Exception as e:
        logger.error("Failed to optimize test suite", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/generate-edge-cases")
async def generate_edge_cases(
    feature_description: str,
    existing_tests: list = [],
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Generate edge case test scenarios"""
    try:
        logger.info("Generating edge cases",
                   feature_description=feature_description[:100],
                   existing_test_count=len(existing_tests),
                   provider=provider)
        
        edge_cases = await test_generator.generate_edge_cases(
            feature_description=feature_description,
            existing_tests=existing_tests,
            provider=provider,
            model=model
        )
        
        return {
            "success": True,
            "message": "Edge cases generated successfully",
            "service_name": "llm-integration",
            "edge_cases": edge_cases
        }
        
    except Exception as e:
        logger.error("Failed to generate edge cases", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/analyze-test-results")
async def analyze_test_results(
    test_results: dict,
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Analyze test execution results and provide insights"""
    try:
        logger.info("Analyzing test results",
                   total_tests=test_results.get("total_tests", 0),
                   failed_tests=test_results.get("failed_tests", 0),
                   provider=provider)
        
        analysis = await test_generator.analyze_test_results(
            test_results=test_results,
            provider=provider,
            model=model
        )
        
        return {
            "success": True,
            "message": "Test results analyzed successfully",
            "service_name": "llm-integration",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error("Failed to analyze test results", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/generate-bug-reproduction-steps")
async def generate_bug_reproduction_steps(
    bug_description: str,
    error_logs: str = "",
    screenshot_analysis: dict = None,
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Generate detailed bug reproduction steps"""
    try:
        logger.info("Generating bug reproduction steps",
                   bug_description=bug_description[:100],
                   has_logs=bool(error_logs),
                   has_screenshot=bool(screenshot_analysis),
                   provider=provider)
        
        reproduction_steps = await test_generator.generate_bug_reproduction_steps(
            bug_description=bug_description,
            error_logs=error_logs,
            screenshot_analysis=screenshot_analysis,
            provider=provider,
            model=model
        )
        
        return {
            "success": True,
            "message": "Bug reproduction steps generated successfully",
            "service_name": "llm-integration",
            "reproduction_steps": reproduction_steps
        }
        
    except Exception as e:
        logger.error("Failed to generate bug reproduction steps", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/llm/providers")
async def get_available_providers():
    """Get list of available LLM providers and their status"""
    try:
        providers = await llm_manager.get_available_providers()
        
        return {
            "success": True,
            "message": "Available providers retrieved successfully",
            "service_name": "llm-integration",
            "providers": providers
        }
        
    except Exception as e:
        logger.error("Failed to get providers", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/llm/prompts")
async def get_available_prompts():
    """Get list of available prompt templates"""
    try:
        prompts = await prompt_manager.get_available_prompts()
        
        return {
            "success": True,
            "message": "Available prompts retrieved successfully",
            "service_name": "llm-integration",
            "prompts": prompts
        }
        
    except Exception as e:
        logger.error("Failed to get prompts", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/llm/custom-prompt")
async def execute_custom_prompt(
    template_name: str,
    variables: dict,
    provider: str = "openai",
    model: str = "gpt-4"
):
    """Execute a custom prompt template with variables"""
    try:
        logger.info("Executing custom prompt",
                   template_name=template_name,
                   variable_count=len(variables),
                   provider=provider)
        
        result = await prompt_manager.execute_prompt(
            template_name=template_name,
            variables=variables,
            provider=provider,
            model=model,
            llm_manager=llm_manager
        )
        
        return {
            "success": True,
            "message": "Custom prompt executed successfully",
            "service_name": "llm-integration",
            "result": result
        }
        
    except Exception as e:
        logger.error("Failed to execute custom prompt", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    config = LLMIntegrationConfig()
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
        reload=config.debug
    )