# Computer Vision Service

Advanced computer vision capabilities for QA automation including OCR text extraction, UI component detection, and accessibility analysis.

## 🎯 Overview

The Computer Vision Service provides intelligent visual analysis capabilities for automated testing:

- **OCR Text Extraction** - Extract text from images using multiple OCR engines
- **UI Component Detection** - Identify and classify UI components (buttons, inputs, etc.)
- **Accessibility Analysis** - WCAG compliance checking and accessibility scoring
- **Visual Comparison** - Advanced image comparison for regression testing
- **Multi-Engine Processing** - Supports Tesseract and EasyOCR with fallbacks

## 🚀 Quick Start

### Start the Service
```bash
# Make sure you're in the computer-vision directory
./start.sh
```

The service will be available at: http://localhost:8004

### Run Tests
```bash
python test_computer_vision.py
```

### Run Demo
```bash
python demo_computer_vision.py
```

## 📋 API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /status` - Detailed service status with capabilities
- `GET /capabilities` - Available features and supported formats

### OCR Text Extraction
- `POST /ocr/extract-text` - Extract text from uploaded image
- `POST /ocr/extract-region` - Extract text from specific region
- `POST /ocr/batch-extract` - Process multiple images concurrently

### Component Detection
- `POST /components/detect` - Detect UI components in image

### Accessibility Analysis
- `POST /accessibility/analyze` - Comprehensive accessibility analysis

## 🔧 Configuration

Key configuration options in `config.py`:

```python
# OCR Configuration
ocr_confidence_threshold: float = 60.0  # Minimum confidence for results
ocr_languages: List[str] = ["eng", "spa", "fra", "deu", "ita", "por"]

# Component Detection
component_detection_confidence: float = 0.5  # Detection confidence threshold

# Accessibility
min_contrast_ratio_aa: float = 4.5   # WCAG AA contrast ratio
min_contrast_ratio_aaa: float = 7.0  # WCAG AAA contrast ratio
min_text_size_pt: float = 12.0       # Minimum text size

# File Processing
max_file_size_mb: int = 50  # Maximum upload size
supported_image_formats: List[str] = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]
```

## 🧪 Usage Examples

### Extract Text from Image
```bash
curl -X POST http://localhost:8004/ocr/extract-text \
  -F "image_file=@screenshot.png" \
  -F "language=eng" \
  -F "engine=auto"
```

### Detect UI Components
```bash
curl -X POST http://localhost:8004/components/detect \
  -F "image_file=@ui_mockup.png" \
  -F "component_types=button,input,checkbox"
```

### Analyze Accessibility
```bash
curl -X POST http://localhost:8004/accessibility/analyze \
  -F "image_file=@webpage.png" \
  -F "wcag_level=AA" \
  -F "include_ocr=true"
```

## 🏗️ Architecture

```
Computer Vision Service
├── main.py                    # FastAPI service with REST endpoints
├── ocr_processor.py          # OCR text extraction (Tesseract + EasyOCR)
├── component_detector.py     # UI component detection using OpenCV
├── accessibility_analyzer.py # WCAG accessibility compliance analysis
├── visual_comparator.py      # Image comparison for regression testing
├── config.py                 # Service configuration
└── shared/                   # Shared utilities and models
```

## 🔤 OCR Capabilities

### Supported Engines
- **Tesseract** - Traditional OCR with high accuracy for clean text
- **EasyOCR** - Modern neural network-based OCR for complex layouts
- **Auto** - Automatically selects best engine based on results

### Features
- Multi-language support (English, Spanish, French, German, Italian, Portuguese)
- Image preprocessing for improved accuracy
- Bounding box detection for text regions
- Confidence scoring for extracted text
- Batch processing for multiple images

### Example Result
```json
{
  "text": "Welcome to our application",
  "confidence": 92.3,
  "engine": "easyocr",
  "bounding_boxes": [
    {
      "x": 50, "y": 100, "width": 200, "height": 30,
      "text": "Welcome to our application",
      "confidence": 92.3
    }
  ],
  "character_count": 26,
  "word_count": 4
}
```

## 🔲 Component Detection

### Detected Components
- **Buttons** - Various styles and sizes
- **Input Fields** - Text inputs, search boxes
- **Checkboxes** - Selection controls
- **Dropdown Menus** - Select controls with arrows
- **Icons** - Small graphical elements
- **Images** - Embedded pictures and graphics
- **Text Elements** - Labels and content text

### Detection Methods
- **Template Matching** - Comparing against known UI patterns
- **Contour Analysis** - Shape-based component identification
- **Edge Detection** - Boundary-based element recognition
- **MSER** - Text region detection using stable regions

### Example Result
```json
{
  "total_components": 5,
  "component_count": {
    "button": 2,
    "input": 2,
    "checkbox": 1
  },
  "components": [
    {
      "component_type": "button",
      "confidence": 0.85,
      "bounding_box": {"x": 100, "y": 200, "width": 120, "height": 40},
      "center_point": [160, 220],
      "properties": {
        "detection_method": "contour_analysis",
        "aspect_ratio": 3.0
      }
    }
  ]
}
```

## ♿ Accessibility Analysis

### WCAG Guidelines Checked
- **1.4.1 Use of Color** - Information not conveyed by color alone
- **1.4.3 Contrast (Minimum)** - Text contrast ratios (AA: 4.5:1)
- **1.4.4 Resize text** - Text can be resized without loss of functionality
- **1.4.6 Contrast (Enhanced)** - Enhanced contrast ratios (AAA: 7:1)
- **2.5.5 Target Size** - Touch targets are adequate size (44×44px minimum)
- **3.1.5 Reading Level** - Text readability considerations

### Analysis Features
- **Contrast Analysis** - Color contrast ratio calculations
- **Text Size Validation** - Minimum readable font sizes
- **Touch Target Analysis** - Interactive element sizing
- **Color Dependency Check** - Over-reliance on color indicators
- **Overall Accessibility Scoring** - 0-1 score with recommendations

### Example Result
```json
{
  "accessibility_score": 0.75,
  "wcag_level": "AA",
  "issues": [
    {
      "type": "contrast",
      "severity": "warning",
      "message": "Insufficient contrast: 3.2 (minimum 4.5)",
      "wcag_guideline": "1.4.3 Contrast (Minimum)",
      "recommendation": "Increase contrast to at least 4.5:1"
    }
  ],
  "recommendations": [
    "Review and improve color contrast ratios",
    "Ensure compliance with WCAG AA guidelines"
  ]
}
```

## 📊 Performance & Limits

### Processing Capabilities
- **Max File Size**: 50MB per image
- **Concurrent Processing**: 3 images simultaneously
- **Supported Formats**: JPG, PNG, BMP, TIFF, WebP
- **OCR Processing Time**: 1-5 seconds per image
- **Component Detection**: 2-8 seconds depending on complexity

### Optimization Features
- **Image Preprocessing** - Automatic enhancement for better OCR
- **Non-Maximum Suppression** - Removes overlapping detections
- **Confidence Filtering** - Only returns high-quality results
- **Async Processing** - Non-blocking concurrent operations

## 🔧 Installation & Dependencies

### System Requirements
- Python 3.8+
- OpenCV 4.8+
- Tesseract OCR (optional, for enhanced text extraction)

### Python Dependencies
```
fastapi>=0.104.1
opencv-python>=4.8.1
pytesseract>=0.3.10
easyocr>=1.7.0
Pillow>=10.1.0
scikit-image>=0.22.0
numpy>=1.25.2
structlog>=23.2.0
```

### Installation
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Install Python dependencies
pip install -r requirements.txt
```

## 🧪 Testing

### Unit Tests
```bash
# Run basic functionality tests
python test_computer_vision.py
```

### Integration Tests
```bash
# Test with other services
curl http://localhost:8004/health

# Test OCR with sample image
curl -X POST http://localhost:8004/ocr/extract-text \
  -F "image_file=@test_image.png"
```

### Performance Testing
- Processes 100+ images per minute
- Handles concurrent requests efficiently
- Memory usage scales linearly with image size

## 🌐 Integration

### With Other Services
- **Website Analyzer** - Analyze screenshots for text content
- **Visual Engine** - OCR for screenshot comparison metadata
- **Test Executor** - Accessibility validation in automated tests
- **Orchestrator** - Visual intelligence for unified test generation

### API Client Example
```python
import requests

# Extract text from screenshot
with open('screenshot.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8004/ocr/extract-text',
        files={'image_file': f},
        data={'language': 'eng', 'engine': 'auto'}
    )
    
result = response.json()
extracted_text = result['text']
confidence = result['confidence']
```

## 🚨 Error Handling

### Common Issues
- **OCR Engine Not Available** - Service falls back to available engines
- **Invalid Image Format** - Returns 400 with supported formats
- **File Too Large** - Returns 413 with size limits
- **Processing Timeout** - Returns 504 with retry suggestions

### Logging
- Structured logging with JSON format
- Request tracing with unique IDs
- Performance metrics and timing
- Error context and stack traces

## 🔒 Security

### Input Validation
- File type verification
- Size limit enforcement
- Malicious content detection
- Path traversal prevention

### Data Handling
- Temporary file cleanup
- Memory-safe image processing
- No persistent storage of uploaded content
- Configurable retention policies

## 📈 Monitoring

### Health Checks
- `/health` - Basic service availability
- `/status` - Detailed component status
- Engine availability monitoring
- Resource usage tracking

### Metrics
- Processing time per image
- OCR accuracy rates
- Component detection success rates
- Error frequency and types

## 🎯 Future Enhancements

### Planned Features
- **Advanced ML Models** - Custom trained models for specific UI frameworks
- **Batch Visual Comparison** - Compare multiple image sets
- **Real-time Processing** - WebSocket-based streaming analysis
- **Custom Component Templates** - User-defined UI component recognition
- **Enhanced Accessibility** - More WCAG guidelines and automated fixes

### Performance Improvements
- **GPU Acceleration** - CUDA support for faster processing
- **Caching Layer** - Redis-based result caching
- **Load Balancing** - Horizontal scaling support
- **Streaming Processing** - Handle very large images efficiently

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python test_computer_vision.py`
4. Start service: `./start.sh`

### Adding New Features
- Follow existing code patterns
- Add comprehensive tests
- Update API documentation
- Ensure backward compatibility

## 📜 License

This Computer Vision Service is part of the QA Automation Platform.

---

**Computer Vision Service** - Intelligent visual analysis for automated testing 🤖👁️