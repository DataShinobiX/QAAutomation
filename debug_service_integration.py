#!/usr/bin/env python3
"""
Debug Service Integration
Trace what happens in the service integration layer
"""
import asyncio
import sys
import os
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'shared'))

async def debug_service_integration():
    """Debug the service integration workflow"""
    
    print("🔍 DEBUGGING SERVICE INTEGRATION WORKFLOW")
    print("=" * 60)
    
    try:
        from service_integration import ServiceIntegrator
        
        integrator = ServiceIntegrator()
        
        print("\n1. Testing Figma service test generation (the current flow)...")
        try:
            result = await integrator.generate_unified_tests(
                target_url="https://demo.validdo.com/signup",
                figma_file_key="SL2zhCoS31dtNI5YRwti2F"
            )
            
            print(f"Test generation success: {result['success']}")
            
            if result["success"]:
                test_suite = result["data"].get("test_suite")
                if test_suite:
                    print(f"✅ Test suite generated: {test_suite.get('name', 'Unknown')}")
                    print(f"Test suite keys: {list(test_suite.keys())}")
                    
                    if "test_cases" in test_suite:
                        print(f"Test cases found: {len(test_suite['test_cases'])}")
                        for i, tc in enumerate(test_suite.get("test_cases", [])[:3]):
                            print(f"  Test {i+1}: {tc.get('name', 'Unknown')} (type: {tc.get('test_type', 'Unknown')})")
                    elif "ui_tests" in test_suite:
                        print(f"UI tests found: {len(test_suite['ui_tests'])}")
                    else:
                        print("❌ No test_cases or ui_tests found in test_suite")
                        print(f"Available fields: {list(test_suite.keys())}")
                        
                    # Now test execution
                    print(f"\n2. Testing test execution with generated test suite...")
                    execution_result = await integrator.execute_tests(test_suite)
                    
                    print(f"Execution success: {execution_result['success']}")
                    if not execution_result["success"]:
                        print(f"❌ Execution error: {execution_result.get('error', 'Unknown error')}")
                    else:
                        execution = execution_result["data"]["execution"]
                        print(f"✅ Execution completed: {execution.get('status')}")
                        print(f"Tests: {execution.get('total_tests')} total, {execution.get('passed_tests')} passed, {execution.get('failed_tests')} failed")
                        
                else:
                    print("❌ No test_suite found in generation result")
                    print(f"Available data keys: {list(result['data'].keys()) if 'data' in result else 'No data field'}")
            else:
                print(f"❌ Test generation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Service integration test failed: {e}")
            import traceback
            traceback.print_exc()
        
        await integrator.close()
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_service_integration())