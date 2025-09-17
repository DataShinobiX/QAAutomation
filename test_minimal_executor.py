#!/usr/bin/env python3
"""
Test the test executor directly with a minimal test suite
"""
import asyncio
import httpx
import json
import uuid

async def test_executor_directly():
    """Test the test executor with a minimal test suite"""
    
    print("🔍 TESTING TEST EXECUTOR DIRECTLY")
    print("=" * 50)
    
    # Create a minimal test suite with proper UUIDs
    test_suite = {
        "id": str(uuid.uuid4()),
        "name": "Minimal Test Suite",
        "description": "Simple test for debugging",
        "url": "https://demo.validdo.com/signup",
        "test_cases": [
            {
                "id": str(uuid.uuid4()),
                "name": "Test Page Title",
                "description": "Check if page title exists",
                "test_type": "ElementExists",
                "target_element": "title",
                "expected_value": None,
                "actions": [],
                "priority": "Medium"
            },
            {
                "id": str(uuid.uuid4()), 
                "name": "Test Body Element",
                "description": "Check if body element exists",
                "test_type": "ElementExists",
                "target_element": "body",
                "expected_value": None,
                "actions": [],
                "priority": "Medium"
            }
        ],
        "created_at": "2025-09-07T15:48:00Z",
        "updated_at": "2025-09-07T15:48:00Z"
    }
    
    request_data = {
        "test_suite": test_suite
    }
    
    print(f"Test suite: {test_suite['name']}")
    print(f"Test cases: {len(test_suite['test_cases'])}")
    print(f"Target URL: {test_suite['url']}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("\nSending request to test executor...")
            
            response = await client.post(
                "http://localhost:3003/execute",
                json=request_data
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Test execution successful!")
                
                if "execution" in result:
                    execution = result["execution"]
                    print(f"Status: {execution.get('status')}")
                    print(f"Total tests: {execution.get('total_tests')}")
                    print(f"Passed: {execution.get('passed_tests')}")
                    print(f"Failed: {execution.get('failed_tests')}")
                    
                    # Show first few test results
                    if "test_results" in execution:
                        print(f"\nFirst few test results:")
                        for i, test_result in enumerate(execution["test_results"][:3]):
                            print(f"  {i+1}. {test_result.get('test_name')}: {test_result.get('status')}")
                            if test_result.get('status') == 'failed':
                                print(f"     Error: {test_result.get('error_message', 'No error message')}")
                else:
                    print("Response structure:", json.dumps(result, indent=2)[:500])
                    
            else:
                print(f"❌ Test execution failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_executor_directly())