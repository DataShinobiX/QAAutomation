#!/bin/bash

# NLP Processing Service Startup Script

set -e

echo "🧠 Starting NLP Processing Service..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the nlp-service directory."
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
echo "📚 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# Download spaCy models
echo "📥 Downloading spaCy language models..."
python -m spacy download en_core_web_sm || echo "⚠️ Failed to download en_core_web_sm"

# Try to download additional models (optional)
python -m spacy download en_core_web_md 2>/dev/null || echo "ℹ️ en_core_web_md not downloaded (optional)"

# Download NLTK data
echo "📥 Downloading NLTK data..."
python -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True) 
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    print('✅ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠️ NLTK download warning: {e}')
"

# Create model cache directory
echo "📁 Creating model cache directory..."
mkdir -p models

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
export PORT="${PORT:-8003}"

echo "✅ NLP Processing Service setup complete!"
echo ""
echo "🚀 Starting service on port ${PORT}..."
echo "📖 API documentation will be available at: http://localhost:${PORT}/docs"
echo "🔍 Health check: http://localhost:${PORT}/health"
echo ""
echo "ℹ️ First startup may take longer as models are loaded..."

# Start the service
python main.py