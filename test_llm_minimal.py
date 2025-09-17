#!/usr/bin/env python3
"""
Test LLM service with minimal component processing
"""
import asyncio
import sys
import os
import json
import time

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'llm-integration'))

async def test_llm_minimal():
    """Test LLM service with minimal data processing"""
    
    print("🔍 TESTING LLM SERVICE WITH MINIMAL DATA")
    print("=" * 60)
    
    try:
        from config import LLMIntegrationConfig
        from test_generator import IntelligentTestGenerator
        from llm_providers import LLMProviderManager
        
        # Initialize components
        config = LLMIntegrationConfig()
        llm_manager = LLMProviderManager(config)
        test_generator = IntelligentTestGenerator(config, llm_manager)
        
        print("1. Testing basic LLM connection...")
        start_time = time.time()
        
        # Test basic connection
        await llm_manager.test_connections()
        connection_time = time.time() - start_time
        print(f"✅ LLM connection test: {connection_time:.2f}s")
        
        print("\n2. Creating minimal figma analysis data...")
        
        # Create minimal figma analysis (simulating what we get from Figma service)
        minimal_figma_analysis = {
            "name": "Flow 2.0",
            "frames": [
                {
                    "name": "Sign Up Frame",
                    "components": [
                        {
                            "name": "Sign Up",
                            "type": "FRAME", 
                            "characters": None
                        }
                    ]
                }
            ]
        }
        
        print(f"Figma data: {json.dumps(minimal_figma_analysis, indent=2)}")
        print(f"Data size: {len(json.dumps(minimal_figma_analysis))} characters")
        
        print("\n3. Testing LLM test generation with minimal data...")
        start_time = time.time()
        
        try:
            # Test the individual components directly with minimal data
            print("Testing scenario generation...")
            scenarios = await test_generator._generate_test_scenarios_from_design(
                minimal_figma_analysis,
                "https://demo.validdo.com/signup",
                "openai",  # Use "openai" instead of "azure_openai" 
                "gpt-4"
            )
            
            print("Testing UI test generation...")
            ui_tests = await test_generator._generate_ui_tests_from_design(
                minimal_figma_analysis,
                "https://demo.validdo.com/signup",
                "openai",  # Use "openai" instead of "azure_openai"
                "gpt-4"
            )
            
            # Create test suite manually
            from models import TestSuite
            test_suite = TestSuite(
                name=f"AI-Generated Tests - {minimal_figma_analysis.get('name', 'Figma Design')}",
                description="Intelligent tests generated from minimal Figma design analysis using azure_openai",
                url="https://demo.validdo.com/signup",
                ui_tests=ui_tests,
                scenarios=scenarios
            )
            
            generation_time = time.time() - start_time
            print(f"✅ LLM test generation: {generation_time:.2f}s")
            
            print(f"\nGenerated Test Suite:")
            print(f"  Name: {test_suite.name}")
            print(f"  Description: {test_suite.description}")
            print(f"  UI Tests: {len(test_suite.ui_tests)}")
            print(f"  Scenarios: {len(test_suite.scenarios)}")
            
            # Show generated tests
            if test_suite.ui_tests:
                print(f"\nFirst UI Test:")
                ui_test = test_suite.ui_tests[0]
                print(f"  Component: {ui_test.component_name}")
                print(f"  Selector: {ui_test.selector}")
                print(f"  Test Type: {ui_test.test_type}")
            
            if test_suite.scenarios:
                print(f"\nFirst Scenario:")
                scenario = test_suite.scenarios[0]
                print(f"  Name: {scenario.name}")
                print(f"  Steps: {len(scenario.steps)}")
                print(f"  Priority: {scenario.priority}")
            
        except Exception as e:
            generation_time = time.time() - start_time
            print(f"❌ LLM test generation failed: {generation_time:.2f}s")
            print(f"Error: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_minimal())