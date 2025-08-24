#!/bin/bash

echo "🚀 Starting Website Analyzer API test..."

# Start the service in background
cd /Users/paritoshsingh/Documents/codes/vs\ code/Opticus/QAAutomation
RUST_LOG=info cargo run --bin website-analyzer &
SERVICE_PID=$!

echo "⏳ Waiting for service to start..."
sleep 5

echo "🔍 Testing health endpoint..."
curl -s http://localhost:3001/health

echo -e "\n📊 Testing website analysis..."
curl -X POST http://localhost:3001/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  -s | jq '.' || echo "Analysis response received"

echo -e "\n📋 Getting analyses list..."
curl -s http://localhost:3001/analyses | jq '.' || echo "Analyses list received"

echo -e "\n🛑 Stopping service..."
kill $SERVICE_PID

echo "✅ Test completed!"