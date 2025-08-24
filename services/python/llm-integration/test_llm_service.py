#!/usr/bin/env python3
"""
Test script for LLM Integration Service
"""
import asyncio
import sys
import os
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import LLMIntegrationConfig
from llm_providers import LLMProviderManager
from test_generator import IntelligentTestGenerator
from prompt_manager import PromptManager
from rate_limiter import RateLimiter
from models import LLMRequest, LLMProvider


async def test_llm_service():
    """Test LLM service functionality"""
    print("🧪 Testing LLM Integration Service...")
    
    # Initialize configuration
    config = LLMIntegrationConfig()
    print(f"📋 Service: {config.service_name}")
    print(f"🔑 Azure Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'Not set')}")
    
    # Test LLM Provider Manager
    print("\n1️⃣ Testing LLM Provider Manager...")
    llm_manager = LLMProviderManager(config)
    
    try:
        await llm_manager.test_connections()
        print("✅ LLM providers initialized successfully!")
    except Exception as e:
        print(f"❌ LLM provider initialization failed: {e}")
        return False
    
    # Test provider status
    print("\n2️⃣ Testing provider status...")
    try:
        status = await llm_manager.get_provider_status()
        print(f"✅ Provider status retrieved: {list(status.keys())}")
        for provider, provider_status in status.items():
            print(f"   📊 {provider}: {provider_status}")
    except Exception as e:
        print(f"❌ Provider status check failed: {e}")
        return False
    
    # Test available providers
    print("\n3️⃣ Testing available providers...")
    try:
        providers = await llm_manager.get_available_providers()
        print(f"✅ Available providers: {len(providers)}")
        for provider in providers:
            print(f"   🤖 {provider['display_name']}: {provider['available']}")
            print(f"      Models: {', '.join(provider['models'][:3])}...")
    except Exception as e:
        print(f"❌ Available providers check failed: {e}")
        return False
    
    # Test basic text generation
    print("\n4️⃣ Testing basic text generation...")
    try:
        request = LLMRequest(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            prompt="Generate a simple test case for a login button. Keep it brief.",
            max_tokens=200,
            temperature=0.3
        )
        
        response = await llm_manager.generate_text(request)
        print("✅ Text generation successful!")
        print(f"   📝 Generated text: {response.content[:100]}...")
        print(f"   🎯 Tokens used: {response.tokens_used}")
        print(f"   ⏱️  Processing time: {response.processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        return False
    
    # Test Prompt Manager
    print("\n5️⃣ Testing Prompt Manager...")
    prompt_manager = PromptManager()
    
    try:
        prompts = await prompt_manager.get_available_prompts()
        print(f"✅ Prompt templates loaded: {len(prompts)}")
        
        for prompt in prompts[:3]:  # Show first 3
            print(f"   📋 {prompt['name']}: Variables: {prompt['variables']}")
        
    except Exception as e:
        print(f"❌ Prompt manager test failed: {e}")
        return False
    
    # Test edge case generation
    print("\n6️⃣ Testing edge case generation...")
    test_generator = IntelligentTestGenerator(config, llm_manager)
    
    try:
        edge_cases = await test_generator.generate_edge_cases(
            feature_description="User login form with email and password fields",
            existing_tests=[
                {"name": "Valid login", "type": "positive"},
                {"name": "Invalid password", "type": "negative"}
            ],
            provider="openai",
            model="gpt-4"
        )
        
        print(f"✅ Edge cases generated: {len(edge_cases)}")
        if edge_cases:
            first_case = edge_cases[0]
            print(f"   🧪 Sample edge case: {first_case.name}")
            print(f"   📋 Description: {first_case.description[:80]}...")
            print(f"   📝 Steps: {len(first_case.steps)} steps")
        
    except Exception as e:
        print(f"❌ Edge case generation failed: {e}")
        return False
    
    # Test rate limiting
    print("\n7️⃣ Testing rate limiting...")
    rate_limiter = RateLimiter(config)
    
    try:
        # Test rate limit check
        allowed = await rate_limiter.check_rate_limit("generate", "openai")
        print(f"✅ Rate limit check: {'Allowed' if allowed else 'Blocked'}")
        
        # Get rate limit status
        status = await rate_limiter.get_rate_limit_status("openai")
        minute_status = status["current_minute"]
        print(f"   📊 Current minute: {minute_status['count']}/{minute_status['limit']} requests")
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False
    
    # Test custom prompt execution
    print("\n8️⃣ Testing custom prompt execution...")
    try:
        result = await prompt_manager.execute_prompt(
            template_name="edge_case_generation",
            variables={
                "feature_description": "Search functionality",
                "existing_tests": json.dumps([{"name": "Basic search", "type": "functional"}]),
                "test_count": "2"
            },
            provider="openai",
            model="gpt-4",
            llm_manager=llm_manager
        )
        
        print("✅ Custom prompt execution successful!")
        print(f"   📝 Response length: {len(result['response'])} characters")
        print(f"   🎯 Tokens used: {result['tokens_used']}")
        
    except Exception as e:
        print(f"❌ Custom prompt execution failed: {e}")
        return False
    
    print("\n🎉 All LLM service tests passed!")
    return True


async def test_integration_scenario():
    """Test a complete integration scenario"""
    print("\n" + "="*60)
    print("🔗 TESTING COMPLETE INTEGRATION SCENARIO")
    print("="*60)
    
    config = LLMIntegrationConfig()
    llm_manager = LLMProviderManager(config)
    test_generator = IntelligentTestGenerator(config, llm_manager)
    
    try:
        # Simulate generating tests from requirements
        print("\n📋 Testing requirements-to-tests generation...")
        
        sample_requirements = """
        User Story: As a customer, I want to search for products so that I can find what I need quickly.
        
        Acceptance Criteria:
        - Search box is prominently displayed on homepage
        - User can enter search terms and press Enter or click search button
        - Results are displayed within 2 seconds
        - No results found message appears if no matches
        - Search terms are highlighted in results
        """
        
        test_suite = await test_generator.generate_from_requirements(
            requirements_text=sample_requirements,
            target_url="https://example-shop.com",
            provider="openai",
            model="gpt-4"
        )
        
        print("✅ Requirements-to-tests generation successful!")
        print(f"   📊 Test scenarios generated: {len(test_suite.scenarios)}")
        print(f"   🧪 UI tests generated: {len(test_suite.ui_tests)}")
        print(f"   📝 Test suite: {test_suite.name}")
        
        if test_suite.scenarios:
            first_scenario = test_suite.scenarios[0]
            print(f"   🎯 Sample scenario: {first_scenario.name}")
            print(f"   📋 Steps: {len(first_scenario.steps)} steps")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration scenario failed: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 LLM INTEGRATION SERVICE TEST")
    print("=" * 60)
    
    try:
        # Basic service tests
        success = await test_llm_service()
        if not success:
            print("\n❌ Basic LLM service tests failed!")
            exit(1)
        
        # Integration scenario test
        integration_success = await test_integration_scenario()
        if not integration_success:
            print("\n❌ Integration scenario tests failed!")
            exit(1)
        
        print("\n✅ All LLM Integration Service tests passed!")
        print("🎯 Service is ready for production use!")
        exit(0)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())