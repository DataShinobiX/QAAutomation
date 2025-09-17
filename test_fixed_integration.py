#!/usr/bin/env python3
"""
Test Fixed Service Integration
Tests the service integration after the data format fix
"""
import asyncio
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'shared'))

async def test_fixed_integration():
    """Test the service integration with the fixed data transformation"""
    
    print("🔧 TESTING FIXED SERVICE INTEGRATION")
    print("=" * 50)
    
    try:
        from service_integration import ServiceIntegrator
        
        integrator = ServiceIntegrator()
        
        # Test 1: Generate tests using Figma
        print("\n1. Testing unified test generation...")
        test_generation_result = await integrator.generate_unified_tests(
            target_url="https://demo.validdo.com/signup",
            figma_file_key="SL2zhCoS31dtNI5YRwti2F"
        )
        
        print(f"Test generation result: {test_generation_result['success']}")
        
        if test_generation_result["success"]:
            test_suite = test_generation_result["data"]["test_suite"]
            print(f"Generated test suite: {test_suite.get('name', 'Unknown')}")
            print(f"Test cases: {len(test_suite.get('test_cases', []))}")
            
            # Test 2: Execute the generated tests
            print("\n2. Testing test execution with generated tests...")
            execution_result = await integrator.execute_tests(test_suite)
            
            print(f"Test execution result: {execution_result['success']}")
            
            if execution_result["success"]:
                execution = execution_result["data"]["execution"]
                print(f"✅ Test execution completed!")
                print(f"Status: {execution.get('status')}")
                print(f"Total tests: {execution.get('total_tests')}")
                print(f"Passed: {execution.get('passed_tests')}")
                print(f"Failed: {execution.get('failed_tests')}")
                
                # Show individual test results
                for result in execution.get('test_results', []):
                    status_emoji = "✅" if result['status'] == 'Passed' else "❌"
                    print(f"  {status_emoji} {result['test_name']}: {result['status']}")
                    if result.get('error_message'):
                        print(f"    Error: {result['error_message']}")
            else:
                print(f"❌ Test execution failed: {execution_result['error']}")
        else:
            print(f"❌ Test generation failed: {test_generation_result['error']}")
        
        await integrator.close()
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_integration())