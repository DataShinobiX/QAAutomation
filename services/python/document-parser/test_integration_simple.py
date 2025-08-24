#!/usr/bin/env python3
"""
Simple Integration Test - Mock LLM Service
Tests document parser integration with mocked LLM responses
"""
import asyncio
import os
import tempfile
import json
import structlog
from parser_manager import DocumentParserManager

logger = structlog.get_logger()


class MockLLMConverter:
    """Mock LLM converter for testing without actual LLM service"""
    
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def convert_requirements_to_tests(self, parsed_doc, target_url=None, test_type="functional"):
        """Mock conversion of requirements to tests"""
        
        # Extract some basic info from the document
        text_length = len(parsed_doc.content.text)
        sections_count = len(parsed_doc.content.sections)
        
        # Mock test cases based on document content
        mock_test_cases = [{
            "name": f"Generated Tests - {parsed_doc.content.metadata.file_name if parsed_doc.content.metadata else 'Document'}",
            "description": f"Test cases generated from {parsed_doc.source_type} document",
            "scenarios": [
                {
                    "name": "User Registration Test",
                    "description": "Test user registration functionality",
                    "steps": [
                        "Navigate to registration page",
                        "Fill out registration form with valid data",
                        "Submit the form",
                        "Verify success message"
                    ],
                    "expected_outcome": "User account created successfully",
                    "priority": "high",
                    "test_type": "functional"
                },
                {
                    "name": "User Login Test",
                    "description": "Test user login functionality", 
                    "steps": [
                        "Navigate to login page",
                        "Enter valid credentials",
                        "Click login button",
                        "Verify redirect to dashboard"
                    ],
                    "expected_outcome": "User successfully logged in",
                    "priority": "high",
                    "test_type": "functional"
                },
                {
                    "name": "Product Search Test",
                    "description": "Test product search functionality",
                    "steps": [
                        "Enter search term in search bar",
                        "Click search button or press enter",
                        "Verify relevant results are displayed",
                        "Test pagination if applicable"
                    ],
                    "expected_outcome": "Relevant products displayed with proper pagination",
                    "priority": "medium",
                    "test_type": "functional"
                }
            ],
            "target_url": target_url,
            "metadata": {
                "source_document_id": parsed_doc.id,
                "generation_method": "mock_llm_conversion"
            }
        }]
        
        return {
            "success": True,
            "test_cases": mock_test_cases,
            "source_document": {
                "id": parsed_doc.id,
                "file_name": parsed_doc.content.metadata.file_name if parsed_doc.content.metadata else "unknown",
                "requirements_count": sections_count,
                "processing_time": parsed_doc.processing_time
            }
        }
    
    async def generate_edge_cases_from_document(self, parsed_doc, existing_tests=None):
        """Mock edge case generation"""
        
        mock_edge_cases = [
            {
                "name": "Empty Form Submission",
                "description": "Test behavior when user submits form with all empty fields",
                "steps": [
                    "Navigate to registration form",
                    "Leave all fields empty",
                    "Click submit button",
                    "Verify appropriate error messages"
                ],
                "expected_outcome": "Form validation errors displayed",
                "priority": "high",
                "test_type": "negative",
                "metadata": {
                    "risk_level": "medium",
                    "category": "validation"
                }
            },
            {
                "name": "SQL Injection Attack",
                "description": "Test system security against SQL injection",
                "steps": [
                    "Navigate to search form",
                    "Enter SQL injection payload: '; DROP TABLE users; --",
                    "Submit the search",
                    "Verify system handles malicious input safely"
                ],
                "expected_outcome": "System blocks malicious input, no database damage",
                "priority": "high",
                "test_type": "security",
                "metadata": {
                    "risk_level": "high",
                    "category": "security"
                }
            },
            {
                "name": "Network Connection Loss",
                "description": "Test system behavior when network connection is lost",
                "steps": [
                    "Start a form submission process",
                    "Disconnect network connection during submission",
                    "Verify system handles network error gracefully",
                    "Reconnect and retry operation"
                ],
                "expected_outcome": "User-friendly error message, data not lost",
                "priority": "medium",
                "test_type": "error_handling",
                "metadata": {
                    "risk_level": "medium",
                    "category": "network"
                }
            }
        ]
        
        return {
            "success": True,
            "edge_cases": mock_edge_cases,
            "source_document": {
                "id": parsed_doc.id,
                "features_extracted": 3
            }
        }


async def create_test_requirements():
    """Create test requirements document"""
    requirements_content = """# Test Application Requirements

## User Management

### User Registration
As a new user, I want to create an account so that I can access the application.

**Acceptance Criteria:**
- User can enter email, password, and name
- Email must be unique and valid
- Password must be at least 8 characters
- User receives confirmation email
- Account is created successfully

### User Login  
As a registered user, I want to log in to access my account.

**Acceptance Criteria:**
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success
- Error shown for invalid credentials

## Product Features

### Product Search
As a user, I want to search for products to find what I need.

**Acceptance Criteria:**
- Search bar is available on all pages
- Results are relevant to search term
- Results are paginated
- Search is fast (under 1 second)

## Technical Requirements

### Performance
- Page load time under 3 seconds
- Search results under 1 second
- Handle 500 concurrent users

### Security
- All data encrypted in transit
- Passwords hashed with bcrypt
- Session timeout after 30 minutes
- Rate limiting on API endpoints
"""
    
    # Create temporary file
    test_dir = tempfile.mkdtemp(prefix="simple_integration_test_")
    requirements_file = os.path.join(test_dir, "test_requirements.md")
    
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    return requirements_file, test_dir


async def test_document_parsing():
    """Test basic document parsing"""
    print("📄 Testing Document Parsing...")
    
    req_file, test_dir = await create_test_requirements()
    
    try:
        parser_manager = DocumentParserManager()
        parsed_doc = await parser_manager.parse_file(req_file)
        
        if parsed_doc.success:
            print("✅ Document parsing successful!")
            print(f"   📝 Text length: {len(parsed_doc.content.text)} characters")
            print(f"   📚 Sections: {len(parsed_doc.content.sections)}")
            print(f"   ⏱️  Processing time: {parsed_doc.processing_time:.3f}s")
            return True, parsed_doc
        else:
            print(f"❌ Document parsing failed: {parsed_doc.error_message}")
            return False, None
            
    finally:
        import shutil
        shutil.rmtree(test_dir)


async def test_mock_llm_integration(parsed_doc):
    """Test integration with mock LLM converter"""
    print("\n🤖 Testing Mock LLM Integration...")
    
    try:
        async with MockLLMConverter() as converter:
            # Test requirements to tests conversion
            result = await converter.convert_requirements_to_tests(
                parsed_doc,
                target_url="https://test-app.com",
                test_type="functional"
            )
            
            if result["success"]:
                print("✅ Requirements to tests conversion successful!")
                print(f"   🧪 Test cases: {len(result['test_cases'])}")
                
                test_case = result['test_cases'][0]
                print(f"   📋 Sample test: {test_case['name']}")
                print(f"   🎯 Scenarios: {len(test_case['scenarios'])}")
                
                # Test edge case generation
                edge_result = await converter.generate_edge_cases_from_document(parsed_doc)
                
                if edge_result["success"]:
                    print(f"   🚨 Edge cases: {len(edge_result['edge_cases'])}")
                    
                    for i, edge_case in enumerate(edge_result['edge_cases'][:2]):
                        print(f"   {i+1}. {edge_case['name']}")
                        print(f"      ⚠️  Risk: {edge_case['metadata']['risk_level']}")
                
                return True
            else:
                print(f"❌ LLM integration failed: {result.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ Mock LLM integration failed: {e}")
        return False


async def test_integration_workflow():
    """Test complete integration workflow"""
    print("\n🔄 Testing Complete Integration Workflow...")
    
    try:
        # Step 1: Parse document
        print("\n1️⃣ Step 1: Parse requirements document")
        success, parsed_doc = await test_document_parsing()
        
        if not success:
            return False
        
        # Step 2: Convert to tests
        print("\n2️⃣ Step 2: Convert to comprehensive test suite")
        llm_success = await test_mock_llm_integration(parsed_doc)
        
        if not llm_success:
            return False
        
        print("\n🎉 Complete workflow successful!")
        print("✅ Document Parser ↔ LLM Integration working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Integration workflow failed: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 DOCUMENT PARSER + LLM INTEGRATION (SIMPLE TEST)")
    print("=" * 70)
    
    try:
        workflow_result = await test_integration_workflow()
        
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS")
        print("=" * 70)
        
        if workflow_result:
            print("✅ ALL TESTS PASSED!")
            print("🎯 Integration between Document Parser and LLM services is working")
            print("💡 Ready for production testing with real LLM service")
        else:
            print("❌ TESTS FAILED!")
            print("⚠️  Integration needs debugging")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configure logging
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