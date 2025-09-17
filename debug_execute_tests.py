#!/usr/bin/env python3
"""
Debug the execute_tests method directly
"""
import asyncio
import sys
import os
import json
import uuid

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'shared'))

async def debug_execute_tests():
    """Debug the execute_tests method with a minimal test suite"""
    
    print("🔍 DEBUGGING EXECUTE_TESTS METHOD")
    print("=" * 50)
    
    try:
        from service_integration import ServiceIntegrator
        
        integrator = ServiceIntegrator()
        
        # Create a minimal test suite with proper UUIDs
        test_suite = {
            "id": str(uuid.uuid4()),
            "name": "Debug Test Suite",
            "description": "Minimal test suite for debugging",
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
            "created_at": "2025-09-07T15:50:00Z",
            "updated_at": "2025-09-07T15:50:00Z"
        }
        
        print(f"Test suite: {test_suite['name']}")
        print(f"Test suite ID: {test_suite['id']}")
        print(f"Test cases: {len(test_suite['test_cases'])}")
        
        print("\nCalling integrator.execute_tests()...")
        result = await integrator.execute_tests(test_suite)
        
        print(f"Result success: {result.get('success')}")
        
        if result.get('success'):
            print("✅ Test execution successful!")
            execution = result["data"]["execution"]
            print(f"Status: {execution.get('status')}")
            print(f"Total tests: {execution.get('total_tests')}")
            print(f"Passed: {execution.get('passed_tests')}")
            print(f"Failed: {execution.get('failed_tests')}")
            
            if execution.get("failed_tests", 0) > 0:
                print("\nFailed tests:")
                for test_result in execution.get("test_results", []):
                    if test_result.get("status") == "failed":
                        print(f"- {test_result.get('test_name')}: {test_result.get('error_message')}")
        else:
            print(f"❌ Test execution failed: {result.get('error')}")
        
        await integrator.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_execute_tests())