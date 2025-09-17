#!/usr/bin/env python3
"""
Test Service Integration Debugging Script
Simulates the service integration workflow to identify the test execution issue
"""
import asyncio
import httpx
import json
from typing import Dict, Any

async def test_service_integration():
    """Test the complete service integration workflow"""
    
    print("🔍 TESTING SERVICE INTEGRATION WORKFLOW")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # 1. Test Figma service test generation (the way service integration calls it)
        print("\n1. Testing Figma service test generation...")
        try:
            response = await client.post(
                "http://localhost:8001/figma/file/SL2zhCoS31dtNI5YRwti2F/generate-tests",
                params={"target_url": "https://demo.validdo.com/signup"}
            )
            
            if response.status_code == 200:
                figma_response = response.json()
                print(f"✅ Figma test generation successful")
                print(f"Response keys: {list(figma_response.keys())}")
                
                # Check if there's a test_suite field
                if 'test_suite' in figma_response:
                    test_suite = figma_response['test_suite']
                    print(f"Found test_suite with keys: {list(test_suite.keys()) if isinstance(test_suite, dict) else 'Not a dict'}")
                    
                    # Now try to pass this to the test executor
                    print("\n2. Testing test execution with Figma-generated test suite...")
                    try:
                        request_data = {"test_suite": test_suite}
                        exec_response = await client.post(
                            "http://localhost:3003/execute",
                            json=request_data
                        )
                        
                        if exec_response.status_code == 200:
                            result = exec_response.json()
                            execution = result.get("execution", {})
                            print(f"✅ Test execution completed!")
                            print(f"Status: {execution.get('status')}")
                            print(f"Total tests: {execution.get('total_tests')}")
                            print(f"Passed: {execution.get('passed_tests')}")
                            print(f"Failed: {execution.get('failed_tests')}")
                        else:
                            print(f"❌ Test execution failed: {exec_response.status_code}")
                            print(f"Response: {exec_response.text}")
                            
                    except Exception as e:
                        print(f"❌ Test execution error: {e}")
                else:
                    print("❌ No test_suite field in Figma response")
                    print(f"Available fields: {list(figma_response.keys())}")
                    
            else:
                print(f"❌ Figma test generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Figma service test failed: {e}")
        
        # 3. Let's also test the service integration execute_tests method directly
        print("\n3. Testing service integration execute_tests method...")
        try:
            from services.python.shared.service_integration import ServiceIntegrator
            
            integrator = ServiceIntegrator()
            
            # Create a mock test suite that should work
            mock_test_suite = {
                "id": "test-suite-123",
                "name": "Mock Test Suite",
                "description": "Testing service integration", 
                "url": "https://demo.validdo.com/signup",
                "test_cases": [],
                "created_at": "2025-09-06T15:00:00Z",
                "updated_at": "2025-09-06T15:00:00Z"
            }
            
            result = await integrator.execute_tests(mock_test_suite)
            print(f"Service integration result: {result}")
            
            await integrator.close()
            
        except Exception as e:
            print(f"❌ Service integration test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_service_integration())