#!/bin/bash

# Comprehensive Debugging Script for QA Automation Platform
# This teaches you how to systematically debug distributed microservices

echo "🔍 DEBUGGING QA AUTOMATION PLATFORM"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Test Basic Connectivity
echo -e "\n${BLUE}STEP 1: BASIC CONNECTIVITY TESTS${NC}"
echo "=================================="

echo -e "${YELLOW}1.1 Testing Workflow Orchestrator Health${NC}"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nRESPONSE_TIME:%{time_total}s" http://localhost:8008/health)
echo "$HEALTH_RESPONSE"

echo -e "\n${YELLOW}1.2 Testing Service Discovery${NC}"
SERVICE_STATUS=$(curl -s http://localhost:8008/service-status)
echo "$SERVICE_STATUS" | jq '.summary'

# Step 2: Create Test Workflow
echo -e "\n${BLUE}STEP 2: CREATE TEST WORKFLOW${NC}"
echo "============================="

echo -e "${YELLOW}2.1 Creating workflow with verbose output${NC}"
WORKFLOW_RESPONSE=$(curl -v --location 'http://localhost:8008/workflows/complete-qa' \
--header 'Content-Type: application/json' \
--data '{
    "url": "https://demo.validdo.com/signup",
    "figma_file_key": "SL2zhCoS31dtNI5YRwti2F", 
    "test_scope": "full_analysis"
}' 2>&1)

echo "$WORKFLOW_RESPONSE"

# Extract workflow ID
WORKFLOW_ID=$(echo "$WORKFLOW_RESPONSE" | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
echo -e "\n${GREEN}Extracted Workflow ID: $WORKFLOW_ID${NC}"

# Step 3: Test Status Endpoint
echo -e "\n${BLUE}STEP 3: STATUS ENDPOINT TESTING${NC}"
echo "==============================="

echo -e "${YELLOW}3.1 Testing status with verbose output${NC}"
STATUS_RESPONSE=$(curl -v http://localhost:8008/workflows/$WORKFLOW_ID/status 2>&1)
echo "$STATUS_RESPONSE"

# Step 4: Check All Possible Routes
echo -e "\n${BLUE}STEP 4: ROUTE DEBUGGING${NC}"
echo "======================="

echo -e "${YELLOW}4.1 List all available routes from FastAPI${NC}"
curl -s http://localhost:8008/docs | grep -o 'paths":[^}]*' || echo "Could not get OpenAPI spec"

echo -e "\n${YELLOW}4.2 Test different HTTP methods on status endpoint${NC}"
echo "GET method:"
curl -s -w "HTTP_CODE:%{http_code}" http://localhost:8008/workflows/$WORKFLOW_ID/status
echo ""

echo "POST method (should fail):"  
curl -s -w "HTTP_CODE:%{http_code}" -X POST http://localhost:8008/workflows/$WORKFLOW_ID/status
echo ""

echo "PUT method (should fail):"
curl -s -w "HTTP_CODE:%{http_code}" -X PUT http://localhost:8008/workflows/$WORKFLOW_ID/status
echo ""

# Step 5: Log Analysis
echo -e "\n${BLUE}STEP 5: LOG ANALYSIS${NC}"
echo "===================="

echo -e "${YELLOW}5.1 Check if logs are accessible${NC}"
if [[ -f "workflow_orchestrator.log" ]]; then
    echo "Found workflow orchestrator log:"
    tail -20 workflow_orchestrator.log
else
    echo "No log file found - logs might be in stdout/terminal"
fi

# Step 6: Process Analysis
echo -e "\n${BLUE}STEP 6: PROCESS ANALYSIS${NC}"  
echo "========================"

echo -e "${YELLOW}6.1 Check running processes${NC}"
ps aux | grep -E "(python|uvicorn|workflow)" | grep -v grep

echo -e "\n${YELLOW}6.2 Check port usage${NC}"
netstat -an | grep :8008 || lsof -i :8008

# Step 7: Results Summary
echo -e "\n${BLUE}STEP 7: DEBUGGING SUMMARY${NC}"
echo "========================="

echo -e "${GREEN}✅ Workflow ID for further testing: $WORKFLOW_ID${NC}"
echo -e "${YELLOW}Use this for manual testing:${NC}"
echo "curl http://localhost:8008/workflows/$WORKFLOW_ID/status"
echo "curl http://localhost:8008/workflows/$WORKFLOW_ID/results"

echo -e "\n${BLUE}🔍 DEBUGGING TIPS:${NC}"
echo "1. Always use -v flag with curl to see HTTP details"
echo "2. Check HTTP status codes: 404=Not Found, 405=Method Not Allowed, 500=Server Error"  
echo "3. Look at Response Headers to identify the server"
echo "4. Check if the service is actually running on the expected port"
echo "5. Verify the route exists in the FastAPI app"
echo "6. Check logs for detailed error messages"