#!/bin/bash

# Visual Engine Startup Script
# Ensures MinIO is accessible before starting the visual engine

set -e

echo "🎯 Starting Visual Engine with MinIO setup..."

# Check if MinIO is running
echo "📋 Checking MinIO status..."
if ! curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "❌ MinIO is not accessible at localhost:9000"
    echo "   Please start MinIO with: docker compose up -d minio"
    exit 1
fi

echo "✅ MinIO is accessible"

# Check if bucket exists, create if not
echo "🪣 Ensuring bucket exists..."
BUCKET_EXISTS=$(docker exec qa_minio mc ls local/ | grep qa-automation-artifacts || true)
if [ -z "$BUCKET_EXISTS" ]; then
    echo "📦 Creating bucket qa-automation-artifacts..."
    docker exec qa_minio mc mb local/qa-automation-artifacts
else
    echo "✅ Bucket qa-automation-artifacts already exists"
fi

# Set environment variables for better AWS SDK behavior
export AWS_EC2_METADATA_DISABLED=true
export MINIO_ENDPOINT=http://127.0.0.1:9000
export RUST_LOG=info

echo "🚀 Starting Visual Engine..."
echo "   - MinIO Endpoint: $MINIO_ENDPOINT" 
echo "   - Logs: $RUST_LOG"
echo ""

# Start the visual engine
cargo run --bin visual-engine