#!/usr/bin/env python3
"""
Document Parser + LLM Integration Test Suite
Tests the integration between document parsing and AI test generation
"""
import asyncio
import os
import sys
import tempfile
import json
from pathlib import Path
import structlog

# Add shared modules to path
sys.path.insert(0, '../shared')

from llm_integration import DocumentToTestConverter
from parser_manager import DocumentParserManager

logger = structlog.get_logger()


async def create_test_requirements_document():
    """Create a comprehensive requirements document for testing"""
    
    requirements_content = """# E-Commerce Platform Requirements

## User Authentication

### User Story 1: User Registration
As a new user, I want to create an account so that I can make purchases and track orders.

**Acceptance Criteria:**
- User can enter email, password, first name, and last name
- Email must be unique and in valid format
- Password must be at least 8 characters with one uppercase, one lowercase, and one number
- User receives confirmation email after successful registration
- User is automatically logged in after registration
- Registration form validates all fields before submission

### User Story 2: User Login
As a registered user, I want to log in to my account so that I can access my profile and purchase history.

**Acceptance Criteria:**
- User can enter email and password
- System validates credentials against database
- User is redirected to dashboard upon successful login
- Error message displayed for invalid credentials
- Account is locked after 5 failed attempts
- User can reset password via email link

## Product Management

### User Story 3: Product Search
As a customer, I want to search for products so that I can find items I want to purchase.

**Acceptance Criteria:**
- Search bar is visible on all pages
- Search returns relevant results based on product name, description, and tags
- Results are paginated (20 items per page)
- Search supports filters by category, price range, brand, and ratings
- Search history is saved for logged-in users
- Auto-complete suggestions appear after typing 3 characters

### User Story 4: Product Details
As a customer, I want to view detailed product information so that I can make informed purchase decisions.

**Acceptance Criteria:**
- Product page displays name, price, description, specifications, and images
- Multiple product images can be viewed in gallery
- Customer reviews and ratings are displayed
- Stock availability is clearly shown
- Related products are suggested
- Social sharing buttons are available

## Shopping Cart

### User Story 5: Add to Cart
As a customer, I want to add products to my cart so that I can purchase multiple items together.

**Acceptance Criteria:**
- Add to cart button is prominently displayed on product pages
- User can select quantity and product variants (size, color, etc.)
- Cart icon shows number of items and updates in real-time
- Items remain in cart across browser sessions for logged-in users
- Out-of-stock items cannot be added to cart
- User receives confirmation when item is added

### User Story 6: Cart Management
As a customer, I want to modify my cart contents so that I can adjust my order before checkout.

**Acceptance Criteria:**
- User can update quantity of items in cart
- User can remove items from cart
- Cart displays item subtotals and total price including taxes
- Shipping cost is calculated and displayed
- Cart saves automatically as user makes changes
- User can apply discount codes and see updated pricing

## Checkout Process

### User Story 7: Guest Checkout
As a guest user, I want to complete my purchase without creating an account so that I can buy quickly.

**Acceptance Criteria:**
- Guest checkout option is clearly available
- User enters shipping and billing information
- Payment methods include credit card, PayPal, and Apple Pay
- Order confirmation email is sent to provided email address
- Guest receives option to create account after purchase
- All payment information is securely processed

### User Story 8: Order Confirmation
As a customer, I want to receive order confirmation so that I know my purchase was successful.

**Acceptance Criteria:**
- Confirmation page displays order number, items, total, and estimated delivery
- Confirmation email is sent immediately after order completion
- Email includes order tracking information
- User can access order status from account dashboard
- Order appears in purchase history
- PDF receipt is available for download

## Technical Requirements

### Performance Requirements
- Page load time must be under 3 seconds on desktop
- Search results must return within 1 second
- System must handle 1,000 concurrent users
- Database queries must complete within 500ms
- Images must be optimized and cached

### Security Requirements
- All data transmission must be encrypted using HTTPS
- Payment information must comply with PCI DSS standards
- User passwords must be hashed using bcrypt
- Session tokens must expire after 30 minutes of inactivity
- Failed login attempts must be logged and monitored

### Compatibility Requirements
- Website must work on Chrome, Firefox, Safari, and Edge (latest 2 versions)
- Mobile responsive design for tablets and smartphones
- Keyboard navigation support for accessibility
- Screen reader compatibility (WCAG 2.1 AA compliance)
- Support for users with JavaScript disabled (graceful degradation)

## Test Data Requirements

### User Test Data
- Valid email addresses: user@example.com, test.user@email.com
- Invalid emails: invalid-email, @domain.com, user@
- Strong passwords: MyP@ssw0rd123, Secure2024!
- Weak passwords: 123, password, abc123

### Product Test Data
- Product categories: Electronics, Clothing, Books, Home & Garden
- Price ranges: $0-25, $25-100, $100-500, $500+
- Product names: "iPhone 15 Pro", "Gaming Laptop", "Running Shoes"
- Stock levels: In Stock (100+), Low Stock (1-10), Out of Stock (0)

### Payment Test Data
- Valid test credit cards: 4111 1111 1111 1111 (Visa), 5555 5555 5555 4444 (Mastercard)
- Invalid cards: 1234 1234 1234 1234, expired cards
- Test PayPal accounts: buyer@example.com / password123

## Error Scenarios

### System Error Handling
- Database connection failures
- Payment gateway timeouts
- Image loading failures
- Search service unavailable
- Inventory service down

### User Error Scenarios
- Duplicate email registration attempts
- Invalid password reset tokens
- Expired session tokens
- Cart items becoming unavailable during checkout
- Payment declined by bank
"""
    
    # Create temporary file
    test_dir = tempfile.mkdtemp(prefix="llm_integration_test_")
    requirements_file = os.path.join(test_dir, "ecommerce_requirements.md")
    
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    return requirements_file, test_dir


async def test_document_to_tests_conversion():
    """Test converting requirements document to test cases"""
    print("🧪 Testing Document to Tests Conversion...")
    
    # Create test document
    req_file, test_dir = await create_test_requirements_document()
    
    try:
        # Parse the requirements document
        print("\n1️⃣ Parsing requirements document...")
        parser_manager = DocumentParserManager()
        parsed_doc = await parser_manager.parse_file(req_file)
        
        if not parsed_doc.success:
            print(f"❌ Document parsing failed: {parsed_doc.error_message}")
            return False
        
        print(f"✅ Document parsed successfully:")
        print(f"   📄 File: ecommerce_requirements.md")
        print(f"   📝 Text length: {len(parsed_doc.content.text)} characters")
        print(f"   📚 Sections: {len(parsed_doc.content.sections)}")
        print(f"   ⏱️  Processing time: {parsed_doc.processing_time:.2f}s")
        
        # Convert to test cases using LLM
        print("\n2️⃣ Converting to test cases using LLM...")
        async with DocumentToTestConverter() as converter:
            result = await converter.convert_requirements_to_tests(
                parsed_doc,
                target_url="https://demo-ecommerce.com",
                test_type="functional"
            )
        
        if not result["success"]:
            print(f"❌ Test conversion failed: {result.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ Test conversion successful:")
        print(f"   🧪 Test cases generated: {len(result['test_cases'])}")
        
        # Display sample test case
        if result["test_cases"]:
            test_case = result["test_cases"][0]
            print(f"   📋 Sample test case: {test_case.name}")
            print(f"   📝 Description: {test_case.description[:100]}...")
            print(f"   🎯 Scenarios: {len(test_case.scenarios)}")
            
            if test_case.scenarios:
                sample_scenario = test_case.scenarios[0]
                print(f"   📊 Sample scenario: {sample_scenario.name}")
                print(f"   📋 Steps: {len(sample_scenario.steps)}")
                print(f"   🏷️  Priority: {sample_scenario.priority}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test conversion failed: {e}")
        return False
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir)


async def test_edge_case_generation():
    """Test generating edge cases from document"""
    print("\n🎯 Testing Edge Case Generation...")
    
    # Create test document
    req_file, test_dir = await create_test_requirements_document()
    
    try:
        # Parse document
        parser_manager = DocumentParserManager()
        parsed_doc = await parser_manager.parse_file(req_file)
        
        if not parsed_doc.success:
            print(f"❌ Document parsing failed")
            return False
        
        # Generate edge cases
        print("\n3️⃣ Generating edge cases...")
        async with DocumentToTestConverter() as converter:
            result = await converter.generate_edge_cases_from_document(
                parsed_doc,
                existing_tests=[]  # No existing tests
            )
        
        if not result["success"]:
            print(f"❌ Edge case generation failed: {result.get('error')}")
            return False
        
        print(f"✅ Edge cases generated successfully:")
        print(f"   🚨 Edge cases: {len(result['edge_cases'])}")
        
        # Display sample edge cases
        for i, edge_case in enumerate(result["edge_cases"][:3]):
            print(f"   {i+1}. {edge_case.name}")
            print(f"      🎯 Category: {edge_case.metadata.get('category', 'unknown')}")
            print(f"      ⚠️  Risk: {edge_case.metadata.get('risk_level', 'unknown')}")
            print(f"      📋 Steps: {len(edge_case.steps)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge case generation failed: {e}")
        return False
        
    finally:
        import shutil
        shutil.rmtree(test_dir)


async def test_test_data_generation():
    """Test generating test data from document"""
    print("\n📊 Testing Test Data Generation...")
    
    # Create test document
    req_file, test_dir = await create_test_requirements_document()
    
    try:
        # Parse document
        parser_manager = DocumentParserManager()
        parsed_doc = await parser_manager.parse_file(req_file)
        
        if not parsed_doc.success:
            print(f"❌ Document parsing failed")
            return False
        
        # Create mock test scenarios
        from llm_integration import TestScenario
        test_scenarios = [
            TestScenario(
                name="User Registration Test",
                description="Test user registration functionality",
                steps=["Navigate to registration page", "Fill out form", "Submit"],
                expected_outcome="User account created successfully"
            ),
            TestScenario(
                name="Product Search Test", 
                description="Test product search functionality",
                steps=["Enter search term", "Click search", "View results"],
                expected_outcome="Relevant products displayed"
            )
        ]
        
        # Generate test data
        print("\n4️⃣ Generating test data...")
        async with DocumentToTestConverter() as converter:
            result = await converter.generate_test_data_from_document(
                parsed_doc,
                test_scenarios
            )
        
        if not result["success"]:
            print(f"❌ Test data generation failed: {result.get('error')}")
            return False
        
        print(f"✅ Test data generated successfully:")
        print(f"   📊 Test data sets: {len(result['test_data'])}")
        
        # Display sample test data
        for i, data_set in enumerate(result["test_data"][:2]):
            print(f"   {i+1}. {data_set.get('name', 'Data Set')}")
            print(f"      📝 Description: {data_set.get('description', 'N/A')[:60]}...")
            print(f"      🎯 Use case: {data_set.get('use_case', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test data generation failed: {e}")
        return False
        
    finally:
        import shutil
        shutil.rmtree(test_dir)


async def test_complete_integration_workflow():
    """Test complete integration workflow"""
    print("\n🔄 Testing Complete Integration Workflow...")
    
    # Create test document
    req_file, test_dir = await create_test_requirements_document()
    
    try:
        # Step 1: Parse document
        print("\n5️⃣ Complete workflow - Step 1: Parse document...")
        parser_manager = DocumentParserManager()
        parsed_doc = await parser_manager.parse_file(req_file)
        
        if not parsed_doc.success:
            print(f"❌ Document parsing failed")
            return False
        
        print(f"✅ Document parsed: {len(parsed_doc.content.sections)} sections")
        
        # Step 2: Generate base test cases
        print("\n6️⃣ Complete workflow - Step 2: Generate base test cases...")
        async with DocumentToTestConverter() as converter:
            test_result = await converter.convert_requirements_to_tests(
                parsed_doc,
                target_url="https://demo-ecommerce.com",
                test_type="functional"
            )
            
            if not test_result["success"]:
                print(f"❌ Base test generation failed")
                return False
            
            print(f"✅ Base tests generated: {len(test_result['test_cases'])} test cases")
            
            # Step 3: Generate edge cases
            print("\n7️⃣ Complete workflow - Step 3: Generate edge cases...")
            edge_result = await converter.generate_edge_cases_from_document(parsed_doc)
            
            if not edge_result["success"]:
                print(f"❌ Edge case generation failed")
                return False
            
            print(f"✅ Edge cases generated: {len(edge_result['edge_cases'])} scenarios")
            
            # Step 4: Generate test data
            print("\n8️⃣ Complete workflow - Step 4: Generate test data...")
            all_scenarios = []
            for test_case in test_result["test_cases"]:
                all_scenarios.extend(test_case.scenarios)
            
            if all_scenarios:
                data_result = await converter.generate_test_data_from_document(
                    parsed_doc,
                    all_scenarios[:3]  # Limit to first 3 scenarios for testing
                )
                
                if data_result["success"]:
                    print(f"✅ Test data generated: {len(data_result['test_data'])} data sets")
                else:
                    print(f"⚠️  Test data generation failed: {data_result.get('error')}")
            
            # Summary
            print(f"\n🎉 Complete workflow successful!")
            print(f"   📄 Document: ecommerce_requirements.md")
            print(f"   📝 Text length: {len(parsed_doc.content.text)} chars")
            print(f"   🧪 Base test cases: {len(test_result['test_cases'])}")
            
            total_scenarios = sum(len(tc.scenarios) for tc in test_result['test_cases'])
            print(f"   📊 Total scenarios: {total_scenarios}")
            print(f"   🚨 Edge cases: {len(edge_result['edge_cases'])}")
            
            if 'data_result' in locals() and data_result.get("success"):
                print(f"   📊 Test data sets: {len(data_result['test_data'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow failed: {e}")
        return False
        
    finally:
        import shutil
        shutil.rmtree(test_dir)


async def test_llm_service_connectivity():
    """Test connectivity to LLM Integration Service"""
    print("\n🔗 Testing LLM Service Connectivity...")
    
    try:
        async with DocumentToTestConverter() as converter:
            # Test simple LLM call
            response = await converter._call_llm_service({
                "provider": "openai",
                "model": "gpt-4",
                "prompt": "Generate a simple test case for user login",
                "max_tokens": 100,
                "temperature": 0.3
            })
            
            if response.get("success"):
                print("✅ LLM service connectivity successful")
                print(f"   🤖 Response length: {len(response.get('content', ''))} chars")
                print(f"   🎯 Tokens used: {response.get('tokens_used', 0)}")
                print(f"   ⏱️  Processing time: {response.get('processing_time', 0):.2f}s")
                return True
            else:
                print(f"❌ LLM service error: {response.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ LLM service connectivity failed: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 80)
    print("🤖 DOCUMENT PARSER + LLM INTEGRATION TEST SUITE")
    print("=" * 80)
    
    test_results = []
    
    try:
        # Test LLM service connectivity first
        connectivity_result = await test_llm_service_connectivity()
        test_results.append(("LLM Service Connectivity", connectivity_result))
        
        if connectivity_result:
            # Run integration tests
            conversion_result = await test_document_to_tests_conversion()
            test_results.append(("Document to Tests Conversion", conversion_result))
            
            edge_case_result = await test_edge_case_generation()
            test_results.append(("Edge Case Generation", edge_case_result))
            
            test_data_result = await test_test_data_generation()
            test_results.append(("Test Data Generation", test_data_result))
            
            workflow_result = await test_complete_integration_workflow()
            test_results.append(("Complete Integration Workflow", workflow_result))
        else:
            print("\n⚠️  Skipping integration tests due to LLM service connectivity issues")
            print("💡 Make sure the LLM Integration Service is running on port 8005")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Tests Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Document Parser + LLM Integration is working perfectly")
        else:
            print("⚠️  Some tests failed - check the logs above")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configure logging for tests
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    asyncio.run(main())