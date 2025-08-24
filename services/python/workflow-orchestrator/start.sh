#!/bin/bash

# Unified Workflow Orchestrator Service Startup Script

set -e

echo "🎯 Starting Unified Workflow Orchestrator Service..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the workflow-orchestrator directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Load environment variables from parent .env file
if [ -f "../.env" ]; then
    echo "📝 Loading environment variables from .env..."
    export $(cat "../.env" | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using system environment variables..."
fi

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../shared"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export PORT="${PORT:-8008}"

echo "✅ Unified Workflow Orchestrator Service setup complete!"
echo ""
echo "🚀 Starting service on port ${PORT}..."
echo "📖 API documentation will be available at: http://localhost:${PORT}/docs"
echo "🔍 Health check: http://localhost:${PORT}/health"
echo ""
echo "🎯 Workflow orchestration endpoints:"
echo "   POST /workflows/start              - Start integrated workflow"
echo "   POST /workflows/start-with-upload  - Start workflow with file upload"
echo "   POST /workflows/quick-test         - Run quick test workflow"
echo "   GET  /workflows/{id}/status        - Get workflow status"
echo "   GET  /workflows/{id}/results       - Get workflow results"
echo "   GET  /service-status               - Check all services health"
echo ""

# Start the service
python main.py