#!/bin/bash
# Start Document Parser Service

set -e

echo "📄 Starting Document Parser Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Load environment variables from parent .env file
if [ -f "../.env" ]; then
    echo "📝 Loading environment variables from .env..."
    export $(cat "../.env" | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using system environment variables..."
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../shared"

# Create upload directory if it doesn't exist
mkdir -p /tmp/uploads

# Start the service
echo "📄 Starting Document Parser service on port 8002..."
python main.py