"""
Shared data models for Python AI services
"""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class BaseResponse(BaseModel):
    """Base response model for all services"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service_name: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: ServiceStatus
    version: str
    uptime: int
    dependencies: Dict[str, ServiceStatus] = {}


# Figma-related models
class FigmaComponent(BaseModel):
    """Figma component data"""
    id: str
    name: str
    type: str
    x: float
    y: float
    width: float
    height: float
    fills: List[Dict[str, Any]] = []
    strokes: List[Dict[str, Any]] = []
    effects: List[Dict[str, Any]] = []
    characters: Optional[str] = None
    style: Dict[str, Any] = {}
    children: List['FigmaComponent'] = []


class FigmaFrame(BaseModel):
    """Figma frame/artboard"""
    id: str
    name: str
    width: float
    height: float
    background_color: Optional[str] = None
    components: List[FigmaComponent] = []


class FigmaDesign(BaseModel):
    """Complete Figma design data"""
    file_key: str
    name: str
    version: str
    frames: List[FigmaFrame] = []
    styles: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Document parsing models
class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    NOTION = "notion"
    CONFLUENCE = "confluence"
    MARKDOWN = "markdown"


class UserStory(BaseModel):
    """Parsed user story"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    acceptance_criteria: List[str] = []
    priority: str = "medium"
    story_points: Optional[int] = None
    tags: List[str] = []
    source_document: str
    page_number: Optional[int] = None


class Requirement(BaseModel):
    """Extracted requirement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    type: str  # functional, non-functional, business-rule
    priority: str = "medium"
    related_stories: List[str] = []
    source: str


class DocumentParseResult(BaseModel):
    """Document parsing result"""
    document_type: DocumentType
    file_name: str
    user_stories: List[UserStory] = []
    requirements: List[Requirement] = []
    metadata: Dict[str, Any] = {}
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# Test generation models
class TestScenario(BaseModel):
    """Generated test scenario"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    steps: List[str] = []
    expected_result: str
    test_type: str  # ui, functional, integration, etc.
    priority: str = "medium"
    source_story: Optional[str] = None
    source_design: Optional[str] = None


class UITestCase(BaseModel):
    """UI-specific test case"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    component_name: str
    selector: str
    test_type: str  # exists, visible, text, style, etc.
    expected_value: Optional[str] = None
    figma_component_id: Optional[str] = None
    screenshot_baseline: Optional[str] = None


class TestSuite(BaseModel):
    """Complete test suite"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    url: str
    ui_tests: List[UITestCase] = []
    scenarios: List[TestScenario] = []
    figma_file_key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Computer vision models
class UIElement(BaseModel):
    """Detected UI element"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # button, input, text, image, etc.
    coordinates: Dict[str, float]  # x, y, width, height
    confidence: float
    text_content: Optional[str] = None
    style_properties: Dict[str, Any] = {}


class VisualAnalysis(BaseModel):
    """Visual analysis result"""
    url: str
    viewport: Dict[str, int]  # width, height
    elements: List[UIElement] = []
    layout_issues: List[str] = []
    accessibility_issues: List[str] = []
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# LLM integration models
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class LLMRequest(BaseModel):
    """LLM request"""
    provider: LLMProvider
    model: str
    prompt: str
    context: Dict[str, Any] = {}
    max_tokens: int = 1000
    temperature: float = 0.7


class LLMResponse(BaseModel):
    """LLM response"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    processing_time: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Document parsing models
class DocumentType(str, Enum):
    """Document type enumeration"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    TEXT = "text"
    NOTION = "notion"
    CONFLUENCE = "confluence"
    HTML = "html"
    MARKDOWN = "markdown"


class DocumentMetadata(BaseModel):
    """Document metadata"""
    file_name: str
    file_size: int
    document_type: DocumentType
    page_count: Optional[int] = None
    creation_date: datetime
    modification_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    custom_metadata: Dict[str, Any] = {}


class DocumentSection(BaseModel):
    """Document section"""
    title: str
    content: str
    metadata: Dict[str, Any] = {}
    subsections: List["DocumentSection"] = []


class DocumentTable(BaseModel):
    """Document table"""
    sheet_name: Optional[str] = None
    table_number: Optional[int] = None
    headers: List[str] = []
    data: List[List[str]] = []


class DocumentImage(BaseModel):
    """Document image"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: Optional[str] = None
    base64_data: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DocumentContent(BaseModel):
    """Parsed document content"""
    text: str
    metadata: Optional[DocumentMetadata] = None
    sections: List[Dict[str, Any]] = []  # Using Dict for flexibility
    tables: List[Dict[str, Any]] = []
    images: List[Dict[str, Any]] = []
    links: List[str] = []


class ParsedDocument(BaseModel):
    """Complete parsed document result"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str  # file, notion, confluence
    source_path: str
    content: DocumentContent
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: float
    parser_version: str
    success: bool
    error_message: Optional[str] = None


class ParsingError(Exception):
    """Custom exception for document parsing errors"""
    pass


# Update forward references
FigmaComponent.model_rebuild()
DocumentSection.model_rebuild()