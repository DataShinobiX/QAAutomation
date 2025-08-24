#!/bin/bash

# Computer Vision Service Startup Script

set -e

echo "🤖 Starting Computer Vision Service..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the computer-vision directory."
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

# Create temp directory
echo "📁 Creating temp directory..."
mkdir -p /tmp/cv_processing

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
export PORT="${PORT:-8004}"

echo "✅ Computer Vision Service setup complete!"
echo ""
echo "🚀 Starting service on port ${PORT}..."
echo "📖 API documentation will be available at: http://localhost:${PORT}/docs"
echo "🔍 Health check: http://localhost:${PORT}/health"
echo ""

# Start the service
python main.py