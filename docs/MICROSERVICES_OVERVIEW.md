# 🔧 Microservices Architecture Overview

## Platform Architecture Summary

Our QA Automation Platform consists of **9 specialized microservices** working together to provide comprehensive, AI-powered testing capabilities. The architecture is split into two main categories:

- **Core Performance Services (Rust)**: Handle browser automation, website analysis, and test execution
- **AI-Powered Services (Python)**: Provide intelligent analysis, document processing, and test generation

---

## 🦀 Core Performance Services (Rust)

### 1. **Website Analyzer Service** 
**Port**: 3001 | **Language**: Rust | **Purpose**: Website DOM Analysis

**What it does:**
- Analyzes website structure using real browser automation (WebDriver)
- Extracts DOM elements, forms, links, and interactive components
- Captures performance metrics (load times, rendering metrics)
- Supports authenticated sessions with cookie management
- Provides fallback HTML parsing when browser unavailable

**Key Features:**
- Real browser rendering for accurate analysis
- JavaScript execution support for SPAs
- Complete DOM structure mapping with XPath/CSS selectors
- Form element detection and validation
- Performance timing analysis

**API Endpoints:**
- `GET /health` - Service health check
- `POST /analyze` - Analyze website structure
- `GET /analyses` - Get analysis history
- `GET /analyses/:id` - Get specific analysis

**Use Case:** "Before running tests, I need to understand what elements exist on the webpage, especially after logging in."

---

### 2. **Visual Engine Service**
**Port**: 3002 | **Language**: Rust | **Purpose**: Screenshot & Visual Testing

**What it does:**
- Captures high-quality screenshots using real browsers
- Performs pixel-perfect visual regression testing
- Supports multiple viewports (desktop, tablet, mobile)
- Stores images in cloud storage (MinIO/S3 compatible)
- Compares images with configurable difference thresholds

**Key Features:**
- Multi-viewport screenshot capture
- Advanced image comparison algorithms
- Cloud storage integration
- Difference visualization and reporting
- Configurable sensitivity settings

**API Endpoints:**
- `GET /health` - Service health check
- `POST /capture` - Capture screenshots
- `POST /compare` - Compare two images
- `GET /screenshots/:id` - Retrieve screenshot
- `GET /visual-tests` - List visual test history

**Use Case:** "I want to ensure my website looks identical across different browsers and screen sizes, especially after UI changes."

---

### 3. **Test Executor Service**
**Port**: 3003 | **Language**: Rust | **Purpose**: Automated Test Execution

**What it does:**
- Executes comprehensive browser-based test suites
- Performs user interactions (click, type, navigate, scroll)
- Validates page elements, content, and behavior
- Supports multiple test types and assertions
- Manages browser sessions and test isolation

**Key Features:**
- Full browser automation capabilities
- Multiple assertion types (element existence, text content, visibility)
- Test suite organization and management
- Detailed test reporting with screenshots
- Parallel test execution support

**API Endpoints:**
- `GET /health` - Service health check
- `POST /execute` - Execute test suite
- `GET /executions/:id` - Get execution results
- `GET /config` - Get execution configuration
- `POST /config` - Update execution settings

**Use Case:** "I have a comprehensive test suite and need to run it automatically across my web application with detailed reporting."

---

## 🐍 AI-Powered Services (Python)

### 4. **Figma Integration Service**
**Port**: 8001 | **Language**: Python | **Purpose**: Design Analysis & Test Generation

**What it does:**
- Connects to Figma API to analyze design files
- Extracts UI components, frames, and design systems
- Identifies interactive elements and their properties
- Generates UI tests based on design specifications
- Maps design elements to test scenarios

**Key Features:**
- Real-time Figma API integration
- Component detection and analysis
- Design asset extraction
- Automated UI test generation
- Design-to-test mapping

**API Endpoints:**
- `GET /health` - Service health check
- `POST /analyze-figma-file` - Analyze Figma design
- `POST /generate-tests` - Generate tests from designs
- `GET /figma-projects` - List available projects
- `GET /generated-tests/{id}` - Retrieve generated tests

**Use Case:** "I have a Figma design for my application and want to automatically generate UI tests that verify the implementation matches the design."

---

### 5. **Document Parser Service**
**Port**: 8002 | **Language**: Python | **Purpose**: Requirements Document Processing

**What it does:**
- Parses multiple document formats (PDF, Word, Excel, PowerPoint, Markdown, Text)
- Integrates with web platforms (Notion, Confluence)
- Extracts structured requirements and user stories
- Identifies acceptance criteria and business rules
- Organizes content into testable specifications

**Key Features:**
- Multi-format document support
- Web API integrations (Notion, Confluence)
- Smart content extraction and categorization
- Requirements structure identification
- Metadata extraction

**API Endpoints:**
- `GET /health` - Service health check
- `POST /parse/upload` - Upload and parse documents
- `POST /parse/file` - Parse local files
- `POST /parse/notion` - Parse Notion pages
- `POST /parse/confluence` - Parse Confluence pages
- `POST /parse-and-generate-tests` - One-step parsing and test generation

**Use Case:** "I have requirements documents in various formats and need to extract testable specifications from them automatically."

---

### 6. **NLP Processing Service**
**Port**: 8003 | **Language**: Python | **Purpose**: Advanced Text Analysis

**What it does:**
- Performs advanced natural language processing on text content
- Extracts named entities, keywords, and semantic relationships
- Analyzes sentiment and text similarity
- Supports multiple languages and text classification
- Provides intelligent text summarization

**Key Features:**
- spaCy and transformers integration
- Named entity recognition
- Sentiment analysis and classification
- Text similarity and clustering
- Multi-language support

**API Endpoints:**
- `GET /health` - Service health check
- `POST /analyze-text` - Analyze text content
- `POST /extract-entities` - Extract named entities
- `POST /classify-text` - Classify text content
- `POST /similarity` - Calculate text similarity

**Use Case:** "I want to analyze user feedback, requirements documents, or test results to extract meaningful insights and patterns."

---

### 7. **Computer Vision Service**
**Port**: 8004 | **Language**: Python | **Purpose**: Image Analysis & OCR

**What it does:**
- Performs OCR (Optical Character Recognition) on screenshots
- Detects UI components and elements in images
- Analyzes visual accessibility features
- Extracts text and data from visual content
- Provides image classification and object detection

**Key Features:**
- Advanced OCR capabilities
- UI element detection in screenshots
- Accessibility analysis
- Image classification and tagging
- Visual content extraction

**API Endpoints:**
- `GET /health` - Service health check
- `POST /ocr` - Extract text from images
- `POST /detect-components` - Detect UI components
- `POST /analyze-accessibility` - Check visual accessibility
- `POST /classify-image` - Classify image content

**Use Case:** "I need to extract text from screenshots, verify UI components are properly displayed, and ensure visual accessibility standards."

---

### 8. **LLM Integration Service**
**Port**: 8005 | **Language**: Python | **Purpose**: AI-Powered Test Generation

**What it does:**
- Integrates with advanced AI models (GPT-4, Claude)
- Generates intelligent test cases from requirements
- Creates edge cases and boundary condition tests
- Provides AI-powered test optimization
- Generates test data and scenarios

**Key Features:**
- Azure OpenAI and Anthropic Claude integration
- Specialized test generation prompts
- Edge case and negative test generation
- Intelligent test data creation
- Multi-provider AI support

**API Endpoints:**
- `GET /health` - Service health check
- `POST /llm/generate` - Generate AI content
- `POST /llm/generate-tests-from-figma` - Generate tests from designs
- `POST /llm/generate-tests-from-requirements` - Generate tests from docs
- `POST /llm/generate-edge-cases` - Generate edge case tests

**Use Case:** "I want AI to automatically generate comprehensive test cases, including edge cases and negative scenarios, from my requirements."

---

### 9. **Smart Unified Test Orchestrator**
**Port**: 8006 | **Language**: Python | **Purpose**: Intelligent Test Unification

**What it does:**
- Combines Figma designs and requirements documents
- Uses AI to map UI elements to business requirements
- Identifies gaps between design and documentation
- Generates comprehensive test suites with 5 categories
- Provides intelligent coverage analysis

**Key Features:**
- Revolutionary unified approach
- AI-powered UI-requirements mapping
- Gap analysis and coverage identification
- 5-category test classification
- Real-time processing under 10 seconds

**API Endpoints:**
- `GET /health` - Service health check
- `POST /generate-unified-tests` - Generate unified test suite
- `POST /generate-unified-tests-upload` - Upload and generate tests
- `GET /service-status` - Check dependent services
- `GET /capabilities` - Service capabilities

**Use Case:** "I have both Figma designs and requirements documents, and I want to generate tests that cover documented features, undocumented UI elements, and identify gaps."

---

### 10. **Authentication Manager Service**
**Port**: 8007 | **Language**: Python | **Purpose**: Web Application Authentication

**What it does:**
- Handles web application login automation
- Supports multiple authentication methods (form-based, OAuth, SAML, Basic Auth)
- Manages MFA/2FA including TOTP
- Maintains secure session management
- Provides authentication state for other services

**Key Features:**
- Multi-method authentication support
- MFA/2FA handling with TOTP
- Secure session and cookie management
- Smart authentication detection
- No persistent credential storage

**API Endpoints:**
- `GET /health` - Service health check
- `POST /authenticate` - Authenticate with website
- `GET /sessions` - List active sessions
- `GET /sessions/{url}/cookies` - Get session cookies
- `POST /test-connection` - Test URL accessibility

**Use Case:** "My application requires login credentials, and I need to authenticate before running any tests while maintaining secure sessions."

---

### 11. **Integrated Workflow Orchestrator**
**Port**: 8008 | **Language**: Python | **Purpose**: Complete End-to-End Coordination

**What it does:**
- Orchestrates complete testing workflows across all services
- Manages authentication, analysis, and test execution sequence
- Provides real-time workflow progress tracking
- Handles error recovery and detailed reporting
- Supports flexible workflow types and configurations

**Key Features:**
- End-to-end workflow coordination
- Real-time progress monitoring
- Intelligent service communication
- Comprehensive error handling
- Flexible workflow configuration

**API Endpoints:**
- `GET /health` - Service health check
- `POST /workflows/start` - Start integrated workflow
- `POST /workflows/start-with-upload` - Start with file upload
- `GET /workflows/{id}/status` - Monitor workflow progress
- `GET /workflows/{id}/results` - Get workflow results
- `GET /service-status` - Check all services health

**Use Case:** "I want to run a complete testing workflow that handles authentication, analyzes my application, processes my requirements, and generates comprehensive tests - all in one coordinated process."

---

## 🔄 How Services Work Together

### **Typical Workflow Sequence:**

1. **Authentication Manager** (8007) → Logs into the web application
2. **Website Analyzer** (3001) → Analyzes the authenticated application structure
3. **Visual Engine** (3002) → Captures screenshots of the application
4. **Document Parser** (8002) → Processes requirements documents
5. **Figma Integration** (8001) → Analyzes design specifications
6. **NLP Processing** (8003) → Extracts insights from text content
7. **Computer Vision** (8004) → Analyzes visual elements
8. **LLM Integration** (8005) → Generates AI-powered test cases
9. **Smart Unified Orchestrator** (8006) → Combines all inputs for unified tests
10. **Test Executor** (3003) → Runs the generated tests
11. **Workflow Orchestrator** (8008) → Coordinates the entire process

### **Service Dependencies:**

```
Workflow Orchestrator (8008)
├── Authentication Manager (8007)
├── Website Analyzer (3001)
├── Visual Engine (3002)
├── Test Executor (3003)
├── Smart Unified Orchestrator (8006)
│   ├── Figma Integration (8001)
│   ├── Document Parser (8002)
│   ├── LLM Integration (8005)
│   ├── NLP Processing (8003)
│   └── Computer Vision (8004)
└── All services coordinate through shared integration layer
```

---

## 🚀 Production Benefits

### **Scalability:**
- Each microservice can be scaled independently
- Horizontal scaling based on demand
- Load balancing across service instances

### **Reliability:**
- Service isolation prevents cascading failures
- Health monitoring and automatic recovery
- Graceful degradation when services are unavailable

### **Flexibility:**
- Services can be used independently or together
- Easy to add new capabilities
- Technology-specific optimizations (Rust for performance, Python for AI)

### **Maintainability:**
- Clear separation of concerns
- Independent development and deployment
- Comprehensive logging and monitoring

This microservices architecture provides a **production-ready, scalable, and intelligent QA automation platform** that can handle real-world testing scenarios with enterprise-grade reliability and performance! 🎯