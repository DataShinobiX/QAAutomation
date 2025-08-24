#!/bin/bash

# Authentication Manager Service Startup Script

set -e

echo "🔐 Starting Authentication Manager Service..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the auth-manager directory."
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

# Check for ChromeDriver (required for Selenium)
echo "🌐 Checking ChromeDriver installation..."
if ! command -v chromedriver &> /dev/null; then
    echo "⚠️ ChromeDriver not found. Installing via webdriver-manager..."
    python -c "
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

print('📥 Downloading ChromeDriver...')
service = Service(ChromeDriverManager().install())
print('✅ ChromeDriver installed successfully')
"
else
    echo "✅ ChromeDriver found"
fi

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
export PORT="${PORT:-8007}"

echo "✅ Authentication Manager Service setup complete!"
echo ""
echo "🚀 Starting service on port ${PORT}..."
echo "📖 API documentation will be available at: http://localhost:${PORT}/docs"
echo "🔍 Health check: http://localhost:${PORT}/health"
echo ""
echo "🔐 Authentication endpoints:"
echo "   POST /authenticate - Authenticate with website"
echo "   GET  /sessions     - List active sessions"
echo "   POST /test-connection - Test URL accessibility"
echo ""

# Start the service
python main.py