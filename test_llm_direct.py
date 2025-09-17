#!/usr/bin/env python3
"""
Test the LLM service directly to debug test generation
"""
import asyncio
import httpx
import json

async def test_llm_service_direct():
    """Test the LLM service generate-tests-from-figma endpoint directly"""
    
    print("🔍 TESTING LLM SERVICE DIRECTLY")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("1. Testing LLM service health...")
            health_response = await client.get("http://localhost:8005/health")
            print(f"Health status: {health_response.status_code}")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"LLM service status: {health_data.get('status')}")
                print(f"Dependencies: {health_data.get('dependencies', {})}")
            
            print("\n2. Testing generate-tests-from-figma endpoint...")
            
            # Make the request to generate tests from Figma
            response = await client.post(
                "http://localhost:8005/llm/generate-tests-from-figma",
                params={
                    "figma_file_key": "SL2zhCoS31dtNI5YRwti2F",
                    "target_url": "https://demo.validdo.com/signup",
                    "provider": "azure_openai",
                    "model": "gpt-4"
                },
                timeout=60.0
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ LLM service request successful!")
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                
                test_suite = result.get("test_suite")
                if test_suite:
                    print(f"\nGenerated Test Suite:")
                    print(f"  Name: {test_suite.get('name')}")
                    print(f"  Description: {test_suite.get('description')}")
                    print(f"  UI Tests: {len(test_suite.get('ui_tests', []))}")
                    print(f"  Scenarios: {len(test_suite.get('scenarios', []))}")
                    
                    # Show first few UI tests
                    ui_tests = test_suite.get('ui_tests', [])[:3]
                    if ui_tests:
                        print(f"\nFirst few UI tests:")
                        for i, test in enumerate(ui_tests):
                            print(f"  {i+1}. {test.get('component_name')}: {test.get('test_type')}")
                else:
                    print("No test_suite in response")
                    print(f"Response keys: {list(result.keys())}")
                    
            else:
                print(f"❌ LLM service request failed: {response.status_code}")
                print(f"Response text: {response.text[:1000]}")
                
    except asyncio.TimeoutError:
        print("❌ Request timed out - LLM service is taking too long")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_service_direct())