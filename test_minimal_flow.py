#!/usr/bin/env python3
"""
Minimal Test Flow
Creates a simple test suite and executes it to verify the flow works
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'shared'))

async def test_minimal_flow():
    """Test with a minimal, properly formatted test suite"""
    
    print("🧪 TESTING MINIMAL EXECUTION FLOW")
    print("=" * 50)
    
    try:
        from service_integration import ServiceIntegrator
        
        integrator = ServiceIntegrator()
        
        # Create a minimal test suite that matches the expected format
        minimal_test_suite = {
            "id": str(uuid.uuid4()),
            "name": "Minimal Test Suite",
            "description": "Basic test suite to verify workflow",
            "url": "https://demo.validdo.com/signup",
            "test_cases": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Check page loads",
                    "description": "Verify the signup page loads successfully",
                    "test_type": "PageTitle",
                    "target_element": None,
                    "expected_value": "Validdo",
                    "actions": [],
                    "priority": "High"
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Check signup form exists", 
                    "description": "Verify signup form is present on page",
                    "test_type": "ElementExists",
                    "target_element": "form",
                    "expected_value": None,
                    "actions": [],
                    "priority": "Medium"
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Check logo exists",
                    "description": "Verify company logo is present",
                    "test_type": "ElementExists", 
                    "target_element": "img[alt='logo']",
                    "expected_value": None,
                    "actions": [],
                    "priority": "Low"
                }
            ],
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        print(f"Created test suite: {minimal_test_suite['name']}")
        print(f"Test cases: {len(minimal_test_suite['test_cases'])}")
        
        # Execute the tests
        print("\n🚀 Executing test suite...")
        execution_result = await integrator.execute_tests(minimal_test_suite)
        
        print(f"Execution success: {execution_result['success']}")
        
        if execution_result["success"]:
            execution = execution_result["data"]["execution"]
            print(f"✅ Test execution completed!")
            print(f"Status: {execution.get('status')}")
            print(f"Total tests: {execution.get('total_tests')}")
            print(f"Passed: {execution.get('passed_tests')}")
            print(f"Failed: {execution.get('failed_tests')}")
            
            # Show individual test results
            for result in execution.get('test_results', []):
                status_emoji = "✅" if result['status'] == 'Passed' else "❌" if result['status'] == 'Failed' else "⚠️"
                print(f"  {status_emoji} {result['test_name']}: {result['status']}")
                if result.get('error_message'):
                    print(f"    Error: {result['error_message']}")
                if result.get('duration_ms'):
                    print(f"    Duration: {result['duration_ms']}ms")
        else:
            print(f"❌ Test execution failed: {execution_result['error']}")
        
        await integrator.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_flow())