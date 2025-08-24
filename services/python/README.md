# Python AI Services

This directory contains the AI/Integration services that provide intelligent test generation and analysis capabilities.

## 🏗️ Architecture

```
services/python/
├── shared/                 # Common utilities and models
├── figma-service/          # Figma design integration
├── document-parser/        # PDF/Word/Notion parsing
├── nlp-service/           # Natural language processing
├── computer-vision/       # Advanced image analysis
├── llm-integration/       # GPT-4/Claude integration
└── orchestrator/          # AI service coordination
```

## 🚀 Services Overview

### 1. Figma Integration Service (Port 8001)
**Status**: ✅ **IMPLEMENTED**

- **Purpose**: Extract UI components, layouts, and design specifications from Figma files
- **Tech Stack**: FastAPI + requests + pydantic + Figma REST API
- **Key Features**:
  - Complete design parsing and component extraction
  - UI test case generation from designs
  - Visual comparison with live websites
  - Style guide extraction (colors, typography, spacing)
  - Screenshot capture and comparison

**Endpoints**:
- `GET /health` - Service health check
- `GET /figma/file/{file_key}` - Get complete Figma file data
- `GET /figma/file/{file_key}/analyze` - Analyze and extract components
- `POST /figma/file/{file_key}/generate-tests` - Generate UI tests
- `GET /figma/file/{file_key}/images` - Get Figma screenshots
- `POST /figma/compare-with-url` - Compare design vs implementation
- `GET /figma/styles/{file_key}` - Extract style guide

### 2. Document Parser Service (Port 8002)
**Status**: 🔄 **PLANNED**

- **Purpose**: Extract requirements from various document formats
- **Tech Stack**: FastAPI + PyPDF2 + python-docx + notion-client
- **Features**: PDF/Word/Notion/Confluence parsing, user story extraction

### 3. NLP Processing Service (Port 8003)
**Status**: 🔄 **PLANNED**

- **Purpose**: Natural language understanding and test case generation
- **Tech Stack**: spaCy + transformers + Custom models
- **Features**: Requirement analysis, edge case identification, test scenario generation

### 4. Computer Vision Service (Port 8004)
**Status**: 🔄 **PLANNED**

- **Purpose**: Advanced image analysis beyond pixel comparison
- **Tech Stack**: OpenCV + Pillow + scikit-image
- **Features**: UI element recognition, layout analysis, accessibility validation

### 5. LLM Integration Service (Port 8005)
**Status**: 🔄 **PLANNED**

- **Purpose**: Intelligent test generation and optimization
- **Tech Stack**: OpenAI GPT-4 + Anthropic Claude + Custom prompts
- **Features**: Context-aware test creation, bug reproduction, result interpretation

### 6. Orchestrator Service (Port 8006)
**Status**: 🔄 **PLANNED**

- **Purpose**: Coordinate all AI services for end-to-end workflows
- **Features**: Service orchestration, workflow management, result aggregation

## 🔧 Setup & Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Active Figma account with API token

### Environment Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Update with your credentials:
```bash
# Required for Figma service
FIGMA_TOKEN=your_figma_token_here
FIGMA_FILE_KEY=your_figma_file_key

# Optional for other services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### Local Development

#### Option 1: Direct Python execution
```bash
# Setup virtual environment
cd services/python/figma-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start service
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../shared"
python main.py
```

#### Option 2: Using Docker Compose
```bash
# Start infrastructure + figma service
docker compose up -d postgres redis minio figma-service

# View logs
docker compose logs -f figma-service
```

### Testing Services

#### Test Figma Service
```bash
cd services/python/figma-service
python test_figma_service.py
```

Expected output:
```
🧪 Testing Figma Integration Service...
✅ Figma API connection successful!
✅ File retrieved: Your Design Name
✅ Analysis completed!
✅ Test generation completed!
✅ Images retrieved!
🎉 All Figma service tests passed!
```

## 📊 Current Implementation Status

| Service | Status | Progress | Key Features |
|---------|---------|----------|--------------|
| **Figma Integration** | ✅ Complete | 100% | Design parsing, test generation, style extraction |
| **Document Parser** | 🔄 Planned | 0% | PDF/Word/Notion parsing |
| **NLP Service** | 🔄 Planned | 0% | Text analysis, requirement extraction |
| **Computer Vision** | 🔄 Planned | 0% | UI element detection, layout analysis |
| **LLM Integration** | 🔄 Planned | 0% | GPT-4/Claude test generation |
| **Orchestrator** | 🔄 Planned | 0% | Service coordination |

## 🔗 Integration with Rust Services

The Python AI services integrate with the core Rust performance services:

- **Website Analyzer** (Port 3001): Provides DOM structure for comparison
- **Visual Engine** (Port 3002): Captures screenshots for visual testing
- **Test Executor** (Port 3003): Executes generated test cases

## 🧪 Testing & Quality Assurance

### Automated Tests
```bash
# Run all Python service tests
cd services/python
python -m pytest

# Run specific service tests
cd figma-service
python test_figma_service.py
```

### Integration Tests
```bash
# Test full workflow: Figma → Test Generation → Execution
# (To be implemented)
```

## 📈 Performance Considerations

- **Figma API**: Rate limited, responses cached for 1 hour
- **Image Processing**: Large designs may take 30+ seconds to process
- **Memory Usage**: ~100-200MB per service
- **Concurrency**: Services handle multiple requests via async/await

## 🚨 Error Handling & Monitoring

- Structured logging via `structlog`
- Health check endpoints for all services
- Graceful fallbacks for API failures
- Prometheus metrics (planned)

## 🔮 Future Enhancements

1. **Real-time Design Sync**: Webhook integration with Figma
2. **Multi-file Support**: Process multiple Figma files simultaneously
3. **Advanced AI Models**: Fine-tuned models for better test generation
4. **Visual Diff Enhancement**: AI-powered visual comparison
5. **Auto-healing Tests**: Self-updating test cases based on design changes

## 🤝 Contributing

1. Follow Python PEP 8 style guidelines
2. Add type hints for all functions
3. Include docstrings for public methods
4. Write unit tests for new features
5. Update this README for new services

## 📚 API Documentation

Each service provides interactive API documentation:
- Figma Service: http://localhost:8001/docs
- Other services: http://localhost:800X/docs (when implemented)

## 🐛 Troubleshooting

### Common Issues

1. **Figma API Connection Failed**
   - Verify FIGMA_TOKEN is correct
   - Check internet connectivity
   - Ensure token has file access permissions

2. **Import Errors**
   - Check PYTHONPATH includes shared directory
   - Verify all dependencies are installed

3. **Docker Build Issues**
   - Clear Docker cache: `docker system prune`
   - Rebuild with: `docker compose build --no-cache figma-service`