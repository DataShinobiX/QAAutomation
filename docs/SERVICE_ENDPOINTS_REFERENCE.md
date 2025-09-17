# 📋 Complete Service Endpoints Reference

## **Fixed Endpoint Mappings**

### **Service Integration Layer Corrections**

| Service | ❌ Wrong Endpoint | ✅ Correct Endpoint | Status |
|---------|------------------|-------------------|--------|
| **Figma Service** | `/analyze-figma-file` | `/figma/file/{file_key}/analyze` | **FIXED** |
| **LLM Integration** | `/analyze` | `/llm/analyze-test-results` | **FIXED** |
| **Document Parser** | `/parse/file` | `/parse/file` | ✅ Correct |
| **Website Analyzer** | `/analyze` | `/analyze` | ✅ Correct |
| **Test Executor** | `/execute` | `/execute` | ✅ Correct |
| **Auth Manager** | `/authenticate` | `/authenticate` | ✅ Correct |
| **Orchestrator** | `/generate-unified-tests` | `/generate-unified-tests` | ✅ Correct |

## **Complete Endpoints Reference**

### **1. Website Analyzer Service (Port 3001)**
- **Health**: `GET /health`
- **Analyze Website**: `POST /analyze`
- **Get Analyses**: `GET /analyses` 
- **Get Analysis by ID**: `GET /analyses/{id}`

### **2. Test Executor Service (Port 3003)**
- **Health**: `GET /health`
- **Execute Tests**: `POST /execute`
- **Get Execution**: `GET /executions/{id}`
- **Get Config**: `GET /config`
- **Update Config**: `POST /config`

### **3. Figma Service (Port 8001)**
- **Health**: `GET /health`
- **Get Figma File**: `GET /figma/file/{file_key}`
- **Analyze Figma File**: `GET /figma/file/{file_key}/analyze` 🔧 **FIXED**
- **Generate Tests from Figma**: `POST /figma/file/{file_key}/generate-tests`
- **Get Figma Images**: `GET /figma/file/{file_key}/images`
- **Compare with URL**: `POST /figma/compare-with-url`
- **Get Styles**: `GET /figma/styles/{file_key}`

### **4. Document Parser Service (Port 8002)**
- **Health**: `GET /health`
- **Parse Upload**: `POST /parse/upload`
- **Parse File**: `POST /parse/file`
- **Batch Parse**: `POST /parse/batch`
- **Parse Notion**: `POST /parse/notion`
- **Parse Confluence**: `POST /parse/confluence`
- **Get Formats**: `GET /formats`
- **Get Capabilities**: `GET /capabilities`
- **Get Stats**: `GET /stats`
- **Get Metadata**: `POST /metadata`
- **Generate Tests from Document**: `POST /generate/tests-from-document`
- **Generate Edge Cases**: `POST /generate/edge-cases`
- **Generate Test Data**: `POST /generate/test-data`
- **Parse and Generate Tests**: `POST /parse-and-generate-tests`
- **Get Document**: `GET /documents/{document_id}`
- **List Documents**: `GET /documents`

### **5. NLP Service (Port 8003)**
- **Health**: `GET /health` ⚠️ **Currently Down**
- **Analyze Text**: `POST /analyze`
- **Extract Entities**: `POST /extract-entities`
- **Generate Test Scenarios**: `POST /generate-test-scenarios`

### **6. Computer Vision Service (Port 8004)**
- **Health**: `GET /health`
- **Analyze Image**: `POST /analyze-image`
- **Compare Screenshots**: `POST /compare-screenshots`
- **Extract Text (OCR)**: `POST /extract-text`

### **7. LLM Integration Service (Port 8005)**
- **Health**: `GET /health`
- **Generate**: `POST /llm/generate`
- **Generate Tests from Figma**: `POST /llm/generate-tests-from-figma`
- **Generate Tests from Requirements**: `POST /llm/generate-tests-from-requirements`
- **Optimize Test Suite**: `POST /llm/optimize-test-suite`
- **Generate Edge Cases**: `POST /llm/generate-edge-cases`
- **Analyze Test Results**: `POST /llm/analyze-test-results` 🔧 **FIXED**
- **Generate Bug Reproduction Steps**: `POST /llm/generate-bug-reproduction-steps`
- **Get Providers**: `GET /llm/providers`
- **Get Prompts**: `GET /llm/prompts`
- **Custom Prompt**: `POST /llm/custom-prompt`

### **8. Orchestrator Service (Port 8006)**
- **Health**: `GET /health`
- **Generate Unified Tests**: `POST /generate-unified-tests`
- **Generate Unified Tests (Upload)**: `POST /generate-unified-tests-upload`
- **Service Status**: `GET /service-status`
- **Capabilities**: `GET /capabilities`

### **9. Auth Manager Service (Port 8007)**
- **Health**: `GET /health`
- **Authenticate**: `POST /authenticate`
- **Get Sessions**: `GET /sessions`
- **Get Session Cookies**: `GET /sessions/{url:path}/cookies`
- **Delete Session**: `DELETE /sessions/{url:path}`
- **Delete All Sessions**: `DELETE /sessions`
- **Validate Session**: `GET /sessions/{url:path}/validate`
- **Test Connection**: `POST /test-connection`
- **Status**: `GET /status`

### **10. Workflow Orchestrator Service (Port 8008)**
- **Health**: `GET /health`
- **Service Status**: `GET /service-status`
- **Start Workflow**: `POST /workflows/start`
- **Complete QA Workflow**: `POST /workflows/complete-qa` 🆕 **NEW**
- **Quick Test**: `POST /workflows/quick-test`
- **Upload Workflow**: `POST /workflows/start-with-upload`
- **Workflow Status**: `GET /workflows/{workflow_id}/status`
- **Workflow Results**: `GET /workflows/{workflow_id}/results`
- **List Workflows**: `GET /workflows`
- **Cancel Workflow**: `DELETE /workflows/{workflow_id}`

## **Test Commands**

### **Test Individual Services:**
```bash
# Test all service health
for port in 3001 3003 8001 8002 8003 8004 8005 8006 8007 8008; do
  echo "Testing port $port:"
  curl -s http://localhost:$port/health | jq '.status // .'
done
```

### **Test Fixed Endpoints:**
```bash
# Test Figma endpoint (FIXED)
curl -s http://localhost:8001/figma/file/SL2zhCoS31dtNI5YRwti2F/analyze | jq '.success'

# Test LLM analyze endpoint (FIXED) 
curl -X POST http://localhost:8005/llm/analyze-test-results \\
  -H "Content-Type: application/json" \\
  -d '{"test_execution_results": {}, "original_inputs": {}}'
```

### **Test Complete QA Workflow:**
```bash
# Create workflow
WORKFLOW_ID=$(curl -s --location 'http://localhost:8008/workflows/complete-qa' \\
--header 'Content-Type: application/json' \\
--data '{
    "url": "https://demo.validdo.com/signup",
    "figma_file_key": "SL2zhCoS31dtNI5YRwti2F",
    "test_scope": "full_analysis"
}' | jq -r '.workflow_id')

echo "Workflow ID: $WORKFLOW_ID"

# Monitor status
curl -s http://localhost:8008/workflows/$WORKFLOW_ID/status | jq '.'
```

## **Changes Made**

### **1. Fixed Figma Service Integration** 
**Before:**
```python
response = await self.client.post(
    f"{figma_service.base_url}/analyze-figma-file",
    json={"figma_file_key": figma_file_key, "generate_tests": True}
)
```

**After:**
```python
response = await self.client.get(
    f"{figma_service.base_url}/figma/file/{figma_file_key}/analyze"
)
```

### **2. Fixed LLM Integration**
**Before:**
```python
response = await self.client.post(
    f"{llm_service.base_url}/analyze",
    json=analysis_request
)
```

**After:**
```python
response = await self.client.post(
    f"{llm_service.base_url}/llm/analyze-test-results",
    json=analysis_request
)
```

## **Current Status** ✅

- ✅ **Figma Service**: Fixed endpoint integration
- ✅ **LLM Integration**: Fixed endpoint integration  
- ⚠️ **NLP Service**: Currently down (non-critical for basic workflow)
- ✅ **All Other Services**: Endpoint mappings verified correct

The complete QA workflow should now work correctly with all endpoint issues resolved!