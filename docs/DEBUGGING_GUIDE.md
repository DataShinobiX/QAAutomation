# 🔍 Complete Debugging Guide for QA Automation Platform

## **Debugging Philosophy: Layer by Layer**

When debugging distributed microservices, think in layers:
```
┌─────────────────────────────────────────┐
│          User/Client Layer              │  ← HTTP requests, curl commands
├─────────────────────────────────────────┤
│         Load Balancer/Proxy             │  ← nginx, traefik (if used)
├─────────────────────────────────────────┤  
│        API Gateway/Router               │  ← FastAPI routing, endpoints
├─────────────────────────────────────────┤
│       Application Logic                 │  ← Your Python code
├─────────────────────────────────────────┤
│      Service Integration               │  ← Inter-service communication
├─────────────────────────────────────────┤
│         Data Storage                   │  ← PostgreSQL, Redis, MinIO
├─────────────────────────────────────────┤
│      Infrastructure                   │  ← Docker, network, ports
└─────────────────────────────────────────┘
```

## **1. HTTP Status Code Analysis**

### **Common Errors and What They Mean:**
- **200 OK**: Request successful ✅
- **400 Bad Request**: Invalid request data (check JSON format)
- **401 Unauthorized**: Authentication required
- **404 Not Found**: Endpoint doesn't exist or resource not found
- **405 Method Not Allowed**: Wrong HTTP method (GET vs POST)
- **422 Unprocessable Entity**: Valid JSON but wrong schema
- **500 Internal Server Error**: Server-side bug
- **502 Bad Gateway**: Service is down or unreachable
- **503 Service Unavailable**: Service overloaded

### **How to Identify the Issue:**
```bash
# Always use verbose mode to see full HTTP exchange
curl -v http://localhost:8008/some-endpoint

# Look for these key indicators:
# > GET /endpoint HTTP/1.1        <- Your request method and path
# < HTTP/1.1 405 Method Not Allowed <- Server response
# < server: uvicorn               <- Which server responded
```

## **2. Systematic Debugging Steps**

### **Step 1: Connectivity Test**
```bash
# Test basic service health
curl -s http://localhost:8008/health

# Test service discovery
curl -s http://localhost:8008/service-status | jq '.summary'
```

### **Step 2: Endpoint Validation**
```bash
# Check if endpoint exists with different methods
curl -s -w "\\nHTTP_CODE:%{http_code}" http://localhost:8008/workflows/test/status
curl -s -w "\\nHTTP_CODE:%{http_code}" -X POST http://localhost:8008/workflows/test/status  
curl -s -w "\\nHTTP_CODE:%{http_code}" -X PUT http://localhost:8008/workflows/test/status
```

### **Step 3: Data Validation**
```bash
# Test with minimal valid data
curl -X POST http://localhost:8008/workflows/complete-qa \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "test_scope": "quick_analysis"}'

# Test with invalid data to see validation errors
curl -X POST http://localhost:8008/workflows/complete-qa \\
  -H "Content-Type: application/json" \\
  -d '{"invalid": "data"}'
```

### **Step 4: Service Chain Analysis**
```bash
# Check each service in the chain
curl -s http://localhost:3001/health  # website-analyzer
curl -s http://localhost:8001/health  # figma-service  
curl -s http://localhost:8005/health  # llm-integration
curl -s http://localhost:8008/health  # workflow-orchestrator
```

## **3. Log Analysis Techniques**

### **Finding Logs in Different Scenarios:**

#### **Terminal/Stdout Logs:**
If services are running in terminals, logs go to stdout:
```bash
# Look at the terminal where you started the service
# Logs will show real-time there
```

#### **File-based Logs:**
```bash
# Common log locations
ls -la *.log
ls -la services/*/logs/
ls -la /var/log/
```

#### **Python Service Logs:**
```bash
# Add this to your Python services for better logging
import structlog
logger = structlog.get_logger()
logger.info("Request received", endpoint="/workflows/status", workflow_id=workflow_id)
```

#### **Docker Logs:**
```bash
# If using Docker
docker logs qa_workflow_orchestrator
docker logs --tail=50 qa_workflow_orchestrator
```

## **4. Advanced Debugging Techniques**

### **4.1 Request Tracing**
Add correlation IDs to track requests across services:
```python
import uuid

# In your FastAPI endpoints
correlation_id = str(uuid.uuid4())
logger.info("Request started", correlation_id=correlation_id, endpoint="/workflows/complete-qa")
```

### **4.2 Service Health Monitoring**
```bash
# Create a monitoring script
while true; do
  echo "$(date): $(curl -s http://localhost:8008/health | jq '.status')"
  sleep 5
done
```

### **4.3 Network Debugging**
```bash
# Check what's listening on ports
netstat -tulpn | grep :8008
lsof -i :8008

# Test connectivity between services
telnet localhost 8008
nc -zv localhost 8008
```

### **4.4 Process Analysis**
```bash
# Find all Python processes
ps aux | grep python | grep -v grep

# Check resource usage
top -p $(pgrep -f "python.*workflow")
```

## **5. Common Issues and Solutions**

### **Issue: 405 Method Not Allowed**
**Cause**: Using wrong HTTP method
**Solution**: Check endpoint definition and use correct method
```python
# In FastAPI
@app.get("/workflows/{workflow_id}/status")  # GET only
@app.post("/workflows/complete-qa")          # POST only  
```

### **Issue: 404 Not Found**  
**Cause**: Endpoint doesn't exist or typo in URL
**Solution**: Verify route registration and URL spelling
```bash
# Check available routes
curl -s http://localhost:8008/docs  # FastAPI auto-docs
curl -s http://localhost:8008/openapi.json | jq '.paths'
```

### **Issue: 422 Unprocessable Entity**
**Cause**: JSON schema validation failed
**Solution**: Check request body format
```python
# Use Pydantic models for validation
class WorkflowRequest(BaseModel):
    url: str
    test_scope: str = "full_analysis"
```

### **Issue: 500 Internal Server Error**
**Cause**: Bug in application code
**Solution**: Check service logs for stack traces

### **Issue: Connection Refused**
**Cause**: Service not running or wrong port
**Solution**: Verify service is running and check port

## **6. Debugging Tools and Scripts**

### **Quick Health Check Script:**
```bash
#!/bin/bash
SERVICES=("3001:website-analyzer" "8001:figma-service" "8005:llm-integration" "8008:workflow-orchestrator")
for service in "${SERVICES[@]}"; do
  port=$(echo $service | cut -d: -f1)
  name=$(echo $service | cut -d: -f2)
  status=$(curl -s -w "%{http_code}" http://localhost:$port/health -o /dev/null)
  if [ "$status" = "200" ]; then
    echo "✅ $name ($port): Healthy"
  else
    echo "❌ $name ($port): Unhealthy ($status)"
  fi
done
```

### **Traffic Analysis Script:**
```bash
#!/bin/bash
# Monitor HTTP traffic (requires tcpdump/wireshark)
sudo tcpdump -i lo0 -A 'port 8008 and (tcp[13] & 0x18 != 0)'
```

## **7. Best Practices for Debugging**

### **7.1 Implement Proper Logging**
```python
import structlog
import time

logger = structlog.get_logger()

@app.post("/workflows/complete-qa")
async def complete_qa_workflow(request: CompleteQARequest):
    start_time = time.time()
    workflow_id = str(uuid.uuid4())
    
    logger.info("Workflow request received", 
                workflow_id=workflow_id,
                url=request.url,
                test_scope=request.test_scope)
    
    try:
        # Your workflow logic
        pass
    except Exception as e:
        logger.error("Workflow failed", 
                    workflow_id=workflow_id, 
                    error=str(e), 
                    traceback=traceback.format_exc())
        raise
    finally:
        execution_time = time.time() - start_time  
        logger.info("Workflow completed",
                   workflow_id=workflow_id,
                   execution_time=execution_time)
```

### **7.2 Use Health Checks Everywhere**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "dependencies": await check_dependencies()
    }

async def check_dependencies():
    # Check database, external APIs, etc.
    return {"database": "healthy", "redis": "healthy"}
```

### **7.3 Environment-specific Debugging**
```bash
# Development
export LOG_LEVEL=DEBUG
export ENABLE_DEBUG=true

# Production  
export LOG_LEVEL=INFO
export ENABLE_DEBUG=false
```

## **8. Your QA Automation Platform Specific Issues**

### **Common Service Issues:**
1. **NLP Service Down**: Check if port 8003 is running
2. **Selenium Issues**: Verify Chrome/WebDriver compatibility  
3. **Authentication Failures**: Check credentials and auth flow
4. **Figma API Limits**: Verify API key and rate limits
5. **Database Connection**: Check PostgreSQL health

### **Workflow-Specific Debugging:**
```bash
# Monitor a specific workflow
WORKFLOW_ID="your-workflow-id"
while true; do
  STATUS=$(curl -s http://localhost:8008/workflows/$WORKFLOW_ID/status | jq -r '.status')
  STEP=$(curl -s http://localhost:8008/workflows/$WORKFLOW_ID/status | jq -r '.current_step')
  echo "$(date): $STATUS - $STEP"
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    break
  fi
  sleep 3
done
```

## **9. Emergency Debugging Checklist**

When something breaks in production:

- [ ] **Check service health endpoints**
- [ ] **Verify all ports are accessible**  
- [ ] **Check recent logs for errors**
- [ ] **Validate request format and data**
- [ ] **Test with minimal/simple requests**
- [ ] **Check external dependencies (databases, APIs)**
- [ ] **Verify environment variables and config**
- [ ] **Test service-to-service communication**
- [ ] **Check resource usage (CPU, memory, disk)**
- [ ] **Validate network connectivity**

Remember: **Always debug systematically, layer by layer!** 🎯