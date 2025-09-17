# QA Automation Orchestrator Guide

## Overview
The orchestrator intelligently coordinates all microservices to provide comprehensive QA automation.

## Your Vision vs Implementation ✅

| Step | Your Requirement | Implementation Status |
|------|------------------|----------------------|
| 1 | User inputs URL, Figma, Auth, Documents | ✅ **IMPLEMENTED** - `/workflows/complete-qa` endpoint |
| 2 | Authentication handling | ✅ **IMPLEMENTED** - auth-manager service integration |
| 3 | Website analyzer call | ✅ **IMPLEMENTED** - website-analyzer service |
| 4 | Figma service analysis | ✅ **IMPLEMENTED** - figma-service integration |
| 5 | Document analysis (NLP) | ✅ **IMPLEMENTED** - document-parser + nlp-service |
| 6 | Smart test generation | ✅ **IMPLEMENTED** - orchestrator service with AI |
| 7 | Test execution | ✅ **IMPLEMENTED** - test-executor service |
| 8 | LLM analysis + reporting | ✅ **IMPLEMENTED** - llm-integration + comprehensive reports |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Orchestrator                        │
│                      (Port: 8008)                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       │    Service Integration        │
       │        Layer                  │
       └─┬─────┬─────┬─────┬─────┬─────┘
         │     │     │     │     │
    ┌────▼┐ ┌──▼──┐ ┌▼───┐ ┌▼───┐ ┌▼────────┐
    │Auth │ │Web  │ │Figma│ │NLP │ │Test Exec│
    │Mgr  │ │Anlyz│ │Svc │ │Svc │ │Service  │
    │8007 │ │3001 │ │8001│ │8003│ │  3003   │
    └─────┘ └─────┘ └────┘ └────┘ └─────────┘
```

## Service Endpoints

### Core Workflow Orchestrator (Port 8008)
- **Main Service**: `http://localhost:8008`
- **Health**: `GET /health`
- **Service Status**: `GET /service-status`
- **Complete QA Workflow**: `POST /workflows/complete-qa` 🎯
- **Quick Test**: `POST /workflows/quick-test`
- **Monitor Workflow**: `GET /workflows/{workflow_id}/status`
- **Get Results**: `GET /workflows/{workflow_id}/results`

## How to Use the Complete QA Workflow

### 1. Basic Website Testing

```bash
curl -X POST http://localhost:8008/workflows/complete-qa \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://demo.validdo.com/signup",
    "test_scope": "full_analysis"
  }'
```

### 2. With Authentication

```bash
curl -X POST http://localhost:8008/workflows/complete-qa \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://yourapp.com/dashboard",
    "credentials": {
      "username": "testuser",
      "password": "testpass",
      "auth_type": "form_based"
    },
    "test_scope": "full_analysis"
  }'
```

### 3. With Figma Design Analysis

```bash
curl -X POST http://localhost:8008/workflows/complete-qa \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://yourapp.com",
    "figma_file_key": "SL2zhCoS31dtNI5YRwti2F",
    "test_scope": "full_analysis"
  }'
```

### 4. Complete Workflow (Your Exact Vision)

```bash
curl -X POST http://localhost:8008/workflows/complete-qa \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://demo.validdo.com/signup",
    "figma_file_key": "SL2zhCoS31dtNI5YRwti2F",
    "credentials": {
      "username": "demo@example.com",
      "password": "demopass"
    },
    "user_stories": [
      "As a user, I want to sign up quickly",
      "As a user, I want clear validation messages"
    ],
    "business_requirements": [
      "Sign up form must be accessible",
      "Form validation should be real-time"
    ],
    "test_scope": "full_analysis",
    "include_accessibility": true,
    "include_performance": true
  }'
```

## Workflow Steps Explanation

### Step 1: Authentication 🔐
- If credentials provided, auth-manager service handles login
- Supports form-based, OAuth, and custom authentication flows
- Returns session cookies and tokens for subsequent requests

### Step 2: Website Analysis 🔍
- website-analyzer service analyzes the URL
- Uses Selenium WebDriver for React/SPA support
- Extracts forms, links, components, and accessibility info

### Step 3: Design Analysis 🎨
- figma-service analyzes the Figma file
- Extracts components, colors, layouts, and design tokens
- Generates design-based test cases

### Step 4: Requirements Analysis 📄
- document-parser processes requirements documents
- nlp-service extracts entities, intents, and test scenarios
- Converts user stories into testable requirements

### Step 5: AI Test Generation 🤖
- orchestrator service combines all inputs intelligently
- Uses LLM to generate comprehensive test suite
- Creates unified, documented, and gap-analysis tests

### Step 6: Test Execution 🧪
- test-executor service runs generated tests
- Executes UI, API, accessibility, and performance tests
- Captures screenshots, logs, and detailed results

### Step 7: AI Analysis 🔬
- llm-integration service analyzes test results
- Provides insights, recommendations, and quality metrics
- Identifies patterns and suggests improvements

### Step 8: Comprehensive Reporting 📊
- Generates detailed QA automation report
- Includes quality metrics, coverage analysis, and recommendations
- Combines all service outputs into actionable insights

## Monitoring Workflow Progress

### Check Status
```bash
curl http://localhost:8008/workflows/{workflow_id}/status
```

**Response:**
```json
{
  "workflow_id": "abc123",
  "status": "running",
  "progress": 65.0,
  "current_step": "🤖 AI-powered test generation",
  "start_time": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:45:00Z"
}
```

### Get Results
```bash
curl http://localhost:8008/workflows/{workflow_id}/results
```

## Error Handling & Fault Tolerance

The orchestrator implements comprehensive error handling:

1. **Service Health Checks**: Validates all services before workflow start
2. **Graceful Degradation**: Continues workflow even if optional services fail  
3. **Detailed Error Reporting**: Specific error messages for each step
4. **Retry Logic**: Automatic retries for transient failures
5. **Circuit Breaker**: Prevents cascade failures

## Quality Metrics

The orchestrator calculates comprehensive quality scores:

- **Test Pass Rate**: Percentage of tests passing
- **Design Compliance Score**: How well implementation matches design
- **Requirements Coverage Score**: Percentage of requirements tested  
- **Overall Quality Score**: Weighted average of all metrics

## Starting All Services

### Using Docker Compose (Recommended)
```bash
# Start core services
docker compose up -d postgres redis minio selenium

# Start all services
docker compose up -d
```

### Manual Start (Development)
```bash
# Terminal 1: Website Analyzer
cd services/website-analyzer && cargo run

# Terminal 2: Test Executor  
cd services/test-executor && cargo run

# Terminal 3: Figma Service
cd services/python/figma-service && python main.py

# Terminal 4: Document Parser
cd services/python/document-parser && python main.py

# Terminal 5: NLP Service
cd services/python/nlp-service && python main.py

# Terminal 6: LLM Integration
cd services/python/llm-integration && python main.py

# Terminal 7: Orchestrator
cd services/python/orchestrator && python main.py

# Terminal 8: Auth Manager
cd services/python/auth-manager && python main.py

# Terminal 9: Workflow Orchestrator (Main)
cd services/python/workflow-orchestrator && python main.py
```

## API Documentation

- **Swagger UI**: `http://localhost:8008/docs`
- **ReDoc**: `http://localhost:8008/redoc`

## System Design Features

### Scalability
- Microservices architecture with independent scaling
- Async processing with background task execution
- Connection pooling and resource management

### Fault Tolerance
- Health checks for all services
- Circuit breaker patterns
- Graceful error handling and recovery

### Observability
- Structured logging with correlation IDs
- Progress tracking with real-time status updates
- Comprehensive metrics and monitoring

### Security
- No secrets in logs or responses
- Authentication token management
- Secure service-to-service communication

## Next Steps

1. **Test the Complete Workflow**: Try the `/workflows/complete-qa` endpoint
2. **Monitor Progress**: Use the status endpoint to track workflow execution  
3. **Review Results**: Check the comprehensive report generated
4. **Scale Services**: Add more instances based on load
5. **Custom Integrations**: Extend with additional services as needed

Your QA automation platform is now **fully functional** and matches your complete vision! 🚀