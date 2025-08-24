#!/bin/bash

echo "🎨 Starting Visual Engine API test..."

# Start the Visual Engine service in background
cd /Users/paritoshsingh/Documents/codes/vs\ code/Opticus/QAAutomation
RUST_LOG=info cargo run --bin visual-engine &
VISUAL_ENGINE_PID=$!

echo "⏳ Waiting for Visual Engine service to start..."
sleep 8

echo "🔍 Testing health endpoint..."
curl -s http://localhost:3002/health

echo -e "\n📸 Testing screenshot capture..."
curl -X POST http://localhost:3002/capture \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "viewports": [
      {"width": 1920, "height": 1080, "device_name": "desktop"},
      {"width": 768, "height": 1024, "device_name": "tablet"}
    ],
    "wait_ms": 1000
  }' \
  -s | jq '.' || echo "Screenshot capture response received"

echo -e "\n📋 Getting visual tests..."
curl -s http://localhost:3002/visual-tests | jq '.' || echo "Visual tests list received"

echo -e "\n🛑 Stopping Visual Engine service..."
kill $VISUAL_ENGINE_PID

echo "✅ Visual Engine API test completed!"