#!/bin/bash

# Smart Unified Test Orchestrator Service Startup Script
set -e

echo "🚀 Starting Smart Unified Test Orchestrator Service..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Make sure you're in the orchestrator directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Load environment variables from parent .env file
if [ -f "../.env" ]; then
    echo "📝 Loading environment variables from .env..."
    export $(cat "../.env" | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using system environment variables..."
fi

# Set environment variables
export PORT=8006
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../shared"

# Check if dependent services are running
echo "🔍 Checking dependent services..."

check_service() {
    local name=$1
    local url=$2
    if curl -s -f "$url/health" > /dev/null 2>&1; then
        echo "✅ $name is running"
        return 0
    else
        echo "⚠️  $name is not responding at $url"
        return 1
    fi
}

# Check dependent services
figma_ok=true
document_ok=true
llm_ok=true

check_service "Figma Service" "http://localhost:8001" || figma_ok=false
check_service "Document Parser Service" "http://localhost:8002" || document_ok=false
check_service "LLM Integration Service" "http://localhost:8005" || llm_ok=false

if [ "$figma_ok" = false ] || [ "$document_ok" = false ] || [ "$llm_ok" = false ]; then
    echo "⚠️  Some dependent services are not running. The orchestrator will start but may not function properly."
    echo "   Please ensure the following services are running:"
    [ "$figma_ok" = false ] && echo "   - Figma Service (port 8001): cd ../figma-service && ./start.sh"
    [ "$document_ok" = false ] && echo "   - Document Parser Service (port 8002): cd ../document-parser && ./start.sh" 
    [ "$llm_ok" = false ] && echo "   - LLM Integration Service (port 8005): cd ../llm-integration && ./start.sh"
    echo ""
fi

# Start the service
echo "🌟 Starting Smart Unified Test Orchestrator Service on port $PORT..."
echo "📋 Service will be available at: http://localhost:$PORT"
echo "📖 API Documentation: http://localhost:$PORT/docs"
echo "💡 Health Check: http://localhost:$PORT/health"
echo "🔗 Service Status: http://localhost:$PORT/service-status"
echo ""
echo "🧪 Example Usage:"
echo "   curl -X POST http://localhost:$PORT/generate-unified-tests-upload \\"
echo "     -F 'figma_file_key=vXiPQiMd1ESraq6wpn1bot' \\"
echo "     -F 'target_url=https://example.com' \\"
echo "     -F 'project_name=My Test Project' \\"
echo "     -F 'requirements_file=@requirements.pdf'"
echo ""
echo "Press Ctrl+C to stop the service"
echo "======================================="

# Start the FastAPI service
python main.py