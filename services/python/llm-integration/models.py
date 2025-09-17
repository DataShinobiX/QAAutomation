"""
Data models for LLM Integration Service
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class LLMProvider(str, Enum):
    """LLM provider enumeration"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    service_name: str = "llm-integration"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseResponse):
    """Health check response"""
    status: ServiceStatus
    version: str
    uptime: float
    dependencies: Dict[str, ServiceStatus] = Field(default_factory=dict)


class LLMRequest(BaseModel):
    """Request model for LLM generation"""
    provider: LLMProvider
    model: str = "gpt-4"
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class LLMResponse(BaseModel):
    """Response model for LLM generation"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    processing_time: float
    
    class Config:
        use_enum_values = True


class TestSuite(BaseModel):
    """Test suite model"""
    id: str = Field(default_factory=lambda: f"suite_{int(datetime.utcnow().timestamp())}")
    name: str
    description: str = ""
    url: str
    figma_file_key: Optional[str] = None
    ui_tests: List[Dict[str, Any]] = Field(default_factory=list)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def dict(self, **kwargs):
        """Override dict to convert to expected format"""
        data = super().dict(**kwargs)
        # Convert ui_tests to test_cases for compatibility
        if self.ui_tests:
            data["test_cases"] = [
                {
                    "id": test.get("id", f"test_{i}"),
                    "name": test.get("component_name", f"Test {i+1}"),
                    "description": f"Test {test.get('component_name', 'component')} - {test.get('test_type', 'unknown')}",
                    "test_type": self._map_test_type(test.get("test_type", "exists")),
                    "target_element": test.get("selector", "*"),
                    "expected_value": test.get("expected_value"),
                    "actions": [],
                    "priority": "Medium"
                }
                for i, test in enumerate(self.ui_tests)
            ]
        return data
    
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


class TestScenario(BaseModel):
    """Test scenario model"""
    id: str = Field(default_factory=lambda: f"scenario_{int(datetime.utcnow().timestamp())}")
    name: str
    description: str = ""
    steps: List[str] = Field(default_factory=list)
    expected_result: str = ""
    test_type: str = "functional"
    priority: str = "medium"
    source_story: Optional[str] = None


class UITestCase(BaseModel):
    """UI test case model"""
    id: str = Field(default_factory=lambda: f"ui_test_{int(datetime.utcnow().timestamp())}")
    component_name: str
    selector: str
    test_type: str = "exists"
    expected_value: Optional[str] = None