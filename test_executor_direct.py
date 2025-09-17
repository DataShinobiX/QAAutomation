#!/usr/bin/env python3
"""
Direct Test Executor Testing Script
Tests the test executor service directly to identify issues
"""
import asyncio
import json
import httpx
from datetime import datetime
import uuid

# Sample test suite that matches the expected TestSuite structure
sample_test_suite = {
    "id": str(uuid.uuid4()),
    "name": "Direct Test Suite",
    "description": "Testing the test executor directly",
    "url": "https://demo.validdo.com/signup",
    "test_cases": [
        {
            "id": str(uuid.uuid4()),
            "name": "Check page title",
            "description": "Verify the page title is correct",
            "test_type": "PageTitle",
            "target_element": None,
            "expected_value": "Validdo",
            "actions": [],
            "priority": "High"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Check signup form exists",
            "description": "Verify signup form is present",
            "test_type": "ElementExists",
            "target_element": "form",
            "expected_value": None,
            "actions": [],
            "priority": "Medium"
        }
    ],
    "created_at": datetime.utcnow().isoformat() + "Z",
    "updated_at": datetime.utcnow().isoformat() + "Z"
}

async def test_executor_directly():
    """Test the executor service directly with sample data"""
    
    print("🧪 TESTING TEST EXECUTOR DIRECTLY")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get("http://localhost:3003/health")
            print(f"Health check: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        
        # 2. Test direct execution with proper data structure
        print("\n2. Testing direct execution...")
        try:
            request_data = {"test_suite": sample_test_suite}
            print(f"Sending test suite: {sample_test_suite['name']}")
            print(f"Test cases: {len(sample_test_suite['test_cases'])}")
            
            response = await client.post(
                "http://localhost:3003/execute",
                json=request_data
            )
            
            print(f"Execution response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                execution = result.get("execution", {})
                print(f"✅ Execution completed!")
                print(f"Status: {execution.get('status')}")
                print(f"Total tests: {execution.get('total_tests')}")
                print(f"Passed: {execution.get('passed_tests')}")
                print(f"Failed: {execution.get('failed_tests')}")
                
                # Print test results
                for test_result in execution.get('test_results', []):
                    print(f"Test '{test_result['test_name']}': {test_result['status']}")
                    if test_result.get('error_message'):
                        print(f"  Error: {test_result['error_message']}")
            else:
                print(f"❌ Execution failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Execution test failed: {e}")
        
        # 3. Test configuration endpoint
        print("\n3. Testing configuration...")
        try:
            response = await client.get("http://localhost:3003/config")
            if response.status_code == 200:
                config = response.json()
                print(f"✅ Configuration retrieved:")
                print(f"Headless: {config.get('headless')}")
                print(f"Viewport: {config.get('viewport')}")
                print(f"Timeout: {config.get('timeout_ms')}ms")
            else:
                print(f"❌ Config retrieval failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Config test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_executor_directly())