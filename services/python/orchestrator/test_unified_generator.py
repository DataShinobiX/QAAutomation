"""
Test Script for Smart Unified Test Generator
Tests the unified approach combining Figma + Requirements + AI
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from smart_unified_generator import SmartUnifiedTestGenerator

# Test data
TEST_FIGMA_FILE_KEY = "vXiPQiMd1ESraq6wpn1bot"
TEST_TARGET_URL = "https://example.com"
TEST_PROJECT_NAME = "Smart Unified Test Demo"

# Sample requirements document content
SAMPLE_REQUIREMENTS = """
# E-Commerce Platform Requirements

## User Stories

As a customer, I want to browse products so that I can find items to purchase.
As a customer, I want to add products to my cart so that I can buy multiple items.
As a customer, I want to checkout securely so that I can complete my purchase.

## Functional Requirements

The system shall provide a product catalog with search and filtering capabilities.
The application must support user authentication and secure login.
Users should be able to view product details including price and availability.

## UI Requirements

The login page must include email field, password field, and submit button.
The product catalog should display products in a grid layout with pagination.
The shopping cart must show item quantities and total price calculation.

## Business Rules

Users cannot checkout without creating an account.
Product prices must be displayed in the user's preferred currency.
Only authenticated users can access their order history.

## Acceptance Criteria

Given a user visits the product catalog, when they apply filters, then results should update immediately.
Given a user adds items to cart, when they view cart, then all items and quantities should be accurate.
Given a user attempts checkout, when they are not logged in, then they should be prompted to login.

## Security Requirements

All user authentication must use HTTPS encryption.
Password fields must mask input characters.
Session tokens must expire after 30 minutes of inactivity.

## Performance Requirements

Product catalog load time must be under 2 seconds.
Search results must return within 500 milliseconds.
The system must support 1000 concurrent users.
"""

async def test_comprehensive_figma_analysis():
    """Test comprehensive Figma analysis"""
    print("🎨 Testing Comprehensive Figma Analysis...")
    
    async with SmartUnifiedTestGenerator() as generator:
        try:
            result = await generator._comprehensive_figma_analysis(TEST_FIGMA_FILE_KEY)
            
            if result["success"]:
                ui_data = result["ui_data"]
                print(f"✅ Figma analysis successful!")
                print(f"   Total Components: {len(ui_data.get('all_components', []))}")
                print(f"   Interactive Elements: {len(ui_data.get('interactive_elements', []))}")
                print(f"   Form Elements: {len(ui_data.get('form_elements', []))}")
                print(f"   Navigation Elements: {len(ui_data.get('navigation_elements', []))}")
                print(f"   Content Elements: {len(ui_data.get('content_elements', []))}")
                print(f"   Visual Elements: {len(ui_data.get('visual_elements', []))}")
                print(f"   Uncategorized Elements: {len(ui_data.get('uncategorized_elements', []))}")
                return True
            else:
                print(f"❌ Figma analysis failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Figma analysis error: {str(e)}")
            return False

async def test_comprehensive_requirements_analysis():
    """Test comprehensive requirements analysis"""
    print("\n📋 Testing Comprehensive Requirements Analysis...")
    
    # Create temporary requirements file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(SAMPLE_REQUIREMENTS)
        temp_file_path = f.name
    
    try:
        async with SmartUnifiedTestGenerator() as generator:
            result = await generator._comprehensive_requirements_analysis(temp_file_path)
            
            if result["success"]:
                req_data = result["requirements_data"]
                print(f"✅ Requirements analysis successful!")
                print(f"   User Stories: {len(req_data.get('user_stories', []))}")
                print(f"   Functional Requirements: {len(req_data.get('functional_requirements', []))}")
                print(f"   UI Requirements: {len(req_data.get('ui_requirements', []))}")
                print(f"   Business Rules: {len(req_data.get('business_rules', []))}")
                print(f"   Acceptance Criteria: {len(req_data.get('acceptance_criteria', []))}")
                print(f"   Security Requirements: {len(req_data.get('security_requirements', []))}")
                print(f"   Performance Requirements: {len(req_data.get('performance_requirements', []))}")
                print(f"   Total Requirements: {len(req_data.get('all_requirements', []))}")
                return True, temp_file_path
            else:
                print(f"❌ Requirements analysis failed: {result.get('error')}")
                return False, temp_file_path
                
    except Exception as e:
        print(f"❌ Requirements analysis error: {str(e)}")
        return False, temp_file_path

async def test_smart_ui_requirement_mapping():
    """Test smart UI-requirement mapping"""
    print("\n🧠 Testing Smart UI-Requirement Mapping...")
    
    # Mock UI data for testing
    mock_ui_data = {
        "all_components": [
            {"name": "LoginButton", "type": "button", "id": "btn_login"},
            {"name": "EmailInput", "type": "input", "id": "input_email"},
            {"name": "PasswordField", "type": "input", "id": "input_password"},
            {"name": "ProductCard", "type": "component", "id": "card_product"},
            {"name": "SearchBar", "type": "input", "id": "search_main"},
            {"name": "CartIcon", "type": "icon", "id": "icon_cart"},
            {"name": "CheckoutButton", "type": "button", "id": "btn_checkout"},
            {"name": "FilterDropdown", "type": "select", "id": "filter_category"},
            {"name": "UndocumentedElement", "type": "button", "id": "btn_mystery"}
        ]
    }
    
    # Mock requirements data
    mock_requirements_data = {
        "all_requirements": [
            {"type": "user_story", "full_text": "As a customer, I want to browse products so that I can find items to purchase", "ui_related": True},
            {"type": "functional_requirement", "text": "The application must support user authentication and secure login", "ui_related": True},
            {"type": "ui_requirement", "text": "The login page must include email field, password field, and submit button", "ui_related": True},
            {"type": "business_rule", "text": "Users cannot checkout without creating an account", "ui_related": True},
            {"type": "requirement_only", "text": "System must send email notifications for order confirmations", "ui_related": False}
        ]
    }
    
    async with SmartUnifiedTestGenerator() as generator:
        try:
            result = await generator._smart_ui_requirement_mapping(mock_ui_data, mock_requirements_data)
            
            print(f"✅ Smart mapping successful!")
            print(f"   Mapped Elements: {len(result.get('mapped_elements', []))}")
            print(f"   Unmapped UI Elements: {len(result.get('unmapped_ui_elements', []))}")
            print(f"   Unmapped Requirements: {len(result.get('unmapped_requirements', []))}")
            
            coverage = result.get("coverage_analysis", {})
            print(f"   UI Coverage: {coverage.get('ui_coverage_percentage', 0)}%")
            print(f"   Requirement Coverage: {coverage.get('requirement_coverage_percentage', 0)}%")
            print(f"   Gaps Identified: {coverage.get('gaps_identified', 0)}")
            
            return True, result
            
        except Exception as e:
            print(f"❌ Smart mapping error: {str(e)}")
            return False, None

async def test_full_unified_generation():
    """Test complete unified test generation"""
    print("\n🚀 Testing Complete Unified Test Generation...")
    
    # Create temporary requirements file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(SAMPLE_REQUIREMENTS)
        temp_file_path = f.name
    
    try:
        async with SmartUnifiedTestGenerator() as generator:
            result = await generator.generate_smart_unified_tests(
                figma_file_key=TEST_FIGMA_FILE_KEY,
                requirements_document_path=temp_file_path,
                target_url=TEST_TARGET_URL,
                project_name=TEST_PROJECT_NAME
            )
            
            if result["success"]:
                print(f"🎉 Complete unified test generation successful!")
                
                coverage = result["coverage_analysis"]
                print(f"   Total Figma Components: {coverage['total_figma_components']}")
                print(f"   Total Requirements: {coverage['total_requirements']}")
                print(f"   Mapped UI Elements: {coverage['mapped_ui_elements']}")
                print(f"   Unmapped UI Elements: {coverage['unmapped_ui_elements']}")
                print(f"   Unmapped Requirements: {coverage['unmapped_requirements']}")
                print(f"   Total Test Cases Generated: {coverage['total_test_cases_generated']}")
                
                categories = result["test_categories"]
                print(f"\n📊 Test Categories:")
                print(f"   Unified Documented Tests: {len(categories['unified_documented_tests'])}")
                print(f"   UI Only Tests: {len(categories['ui_only_tests'])}")
                print(f"   Requirement Only Tests: {len(categories['requirement_only_tests'])}")
                print(f"   Inferred Functionality Tests: {len(categories['inferred_functionality_tests'])}")
                print(f"   Gap Analysis Tests: {len(categories['gap_analysis_tests'])}")
                
                # Save result for inspection
                output_file = "unified_test_result.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"\n💾 Complete result saved to: {output_file}")
                
                return True
            else:
                print(f"❌ Unified test generation failed: {result.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ Unified test generation error: {str(e)}")
        return False
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

async def test_service_availability():
    """Test if all required services are available"""
    print("🔍 Testing Service Availability...")
    
    import httpx
    
    services = {
        "Figma Service": "http://localhost:8001",
        "Document Parser Service": "http://localhost:8002", 
        "LLM Integration Service": "http://localhost:8005"
    }
    
    all_available = True
    
    async with httpx.AsyncClient(timeout=5) as client:
        for service_name, service_url in services.items():
            try:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    print(f"✅ {service_name} is available")
                else:
                    print(f"⚠️  {service_name} responded with status {response.status_code}")
                    all_available = False
            except Exception as e:
                print(f"❌ {service_name} is not available: {str(e)}")
                all_available = False
    
    return all_available

async def main():
    """Run all tests"""
    print("🧪 Smart Unified Test Generator - Comprehensive Test Suite")
    print("=" * 60)
    
    # Test 1: Service Availability
    services_ok = await test_service_availability()
    
    if not services_ok:
        print("\n⚠️  Some services are not available. Tests may fail.")
        print("   Please ensure all services are running:")
        print("   - cd ../figma-service && ./start.sh")
        print("   - cd ../document-parser && ./start.sh") 
        print("   - cd ../llm-integration && ./start.sh")
        print("\n   Continuing with available tests...")
    
    # Test 2: Figma Analysis (if Figma service available)
    figma_ok = await test_comprehensive_figma_analysis()
    
    # Test 3: Requirements Analysis (if Document service available)  
    req_ok, temp_file = await test_comprehensive_requirements_analysis()
    
    # Test 4: Smart Mapping (if LLM service available)
    mapping_ok, mapping_result = await test_smart_ui_requirement_mapping()
    
    # Test 5: Full Integration (if all services available)
    if services_ok:
        full_ok = await test_full_unified_generation()
    else:
        print("\n⚠️  Skipping full integration test due to missing services")
        full_ok = False
    
    # Test Summary
    print("\n" + "=" * 60)
    print("🏁 Test Summary:")
    print(f"   Service Availability: {'✅' if services_ok else '❌'}")
    print(f"   Figma Analysis: {'✅' if figma_ok else '❌'}")
    print(f"   Requirements Analysis: {'✅' if req_ok else '❌'}")
    print(f"   Smart Mapping: {'✅' if mapping_ok else '❌'}")
    print(f"   Full Integration: {'✅' if full_ok else '❌'}")
    
    if all([services_ok, figma_ok, req_ok, mapping_ok, full_ok]):
        print("\n🎉 All tests passed! Smart Unified Test Generator is working correctly.")
        print("\n🚀 You can now:")
        print("   1. Start the orchestrator service: ./start.sh")
        print("   2. Use the unified test generation API")
        print("   3. Generate comprehensive test suites from Figma + Requirements")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("   Make sure all dependent services are running properly.")
    
    # Clean up
    try:
        if 'temp_file' in locals() and temp_file:
            os.unlink(temp_file)
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())