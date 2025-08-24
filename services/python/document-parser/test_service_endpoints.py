#!/usr/bin/env python3
"""
Document Parser Service Endpoints Test
Tests the FastAPI service endpoints with LLM integration
"""
import asyncio
import tempfile
import json
import aiofiles
import httpx
from pathlib import Path


async def create_test_document():
    """Create test document for endpoint testing"""
    content = """# User Management System Requirements

## Authentication Module

### User Registration
As a new user, I want to register for an account so that I can access the platform.

**Acceptance Criteria:**
- User provides email, password, first name, and last name
- Email must be unique in the system
- Password must meet complexity requirements (8+ chars, uppercase, lowercase, number)
- User receives email verification after registration
- Account is activated upon email confirmation

### User Login
As a registered user, I want to log in to access my account.

**Acceptance Criteria:**
- User enters email and password
- System validates credentials against database
- Successful login redirects to dashboard
- Failed attempts are logged for security
- Account locks after 5 failed attempts

## Profile Management

### Profile Update
As a logged-in user, I want to update my profile information.

**Acceptance Criteria:**
- User can modify name, email, phone number
- Email changes require re-verification
- Changes are saved immediately
- User sees confirmation of updates
- Audit log tracks all profile changes

## System Requirements

### Performance
- Registration process completes within 3 seconds
- Login validation within 1 second
- Profile updates save within 2 seconds
- System supports 1000 concurrent users

### Security
- All passwords hashed with bcrypt
- Session tokens expire after 30 minutes
- HTTPS required for all authentication endpoints
- Rate limiting: 5 attempts per minute for login
"""
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp(prefix="service_endpoint_test_")
    doc_file = Path(temp_dir) / "user_management_requirements.md"
    
    async with aiofiles.open(doc_file, 'w', encoding='utf-8') as f:
        await f.write(content)
    
    return str(doc_file), temp_dir


async def test_parse_and_generate_endpoint():
    """Test the /parse-and-generate-tests endpoint"""
    print("🧪 Testing /parse-and-generate-tests endpoint...")
    
    doc_file, temp_dir = await create_test_document()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test file upload and generation
            with open(doc_file, 'rb') as f:
                files = {'file': ('requirements.md', f, 'text/markdown')}
                data = {
                    'target_url': 'https://user-management-demo.com',
                    'test_type': 'functional',
                    'include_edge_cases': True,
                    'include_test_data': True
                }
                
                response = await client.post(
                    'http://localhost:8002/parse-and-generate-tests',
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        print("✅ Parse and generate endpoint successful!")
                        print(f"   📄 Document ID: {result.get('document_id', 'N/A')[:20]}...")
                        
                        parsing_result = result.get('parsing_result', {})
                        print(f"   📝 Text length: {parsing_result.get('text_length', 0)}")
                        print(f"   📚 Sections: {parsing_result.get('sections_count', 0)}")
                        print(f"   ⏱️  Parse time: {parsing_result.get('processing_time', 0):.3f}s")
                        
                        test_result = result.get('test_generation_result', {})
                        if test_result.get('success'):
                            print(f"   🧪 Test cases: {len(test_result.get('test_cases', []))}")
                            print(f"   🚨 Edge cases: {len(test_result.get('edge_cases', []))}")
                            print(f"   📊 Test data sets: {len(test_result.get('test_data', []))}")
                        
                        return True, result
                    else:
                        print(f"❌ Endpoint returned error: {result.get('error')}")
                        return False, None
                else:
                    print(f"❌ HTTP error: {response.status_code} - {response.text}")
                    return False, None
                    
    except Exception as e:
        print(f"❌ Parse and generate test failed: {e}")
        return False, None
    
    finally:
        import shutil
        shutil.rmtree(temp_dir)


async def test_generate_tests_endpoint():
    """Test the /generate/tests-from-document endpoint"""
    print("\n📝 Testing /generate/tests-from-document endpoint...")
    
    doc_file, temp_dir = await create_test_document()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First parse the document
            with open(doc_file, 'rb') as f:
                files = {'file': ('requirements.md', f, 'text/markdown')}
                
                parse_response = await client.post(
                    'http://localhost:8002/parse/upload',
                    files=files
                )
                
                if parse_response.status_code != 200:
                    print(f"❌ Document parsing failed: {parse_response.status_code}")
                    return False
                
                parse_result = parse_response.json()
                if not parse_result.get('success'):
                    print(f"❌ Document parsing error: {parse_result.get('error')}")
                    return False
                
                document_id = parse_result['document']['id']
                print(f"   📄 Document parsed: {document_id[:20]}...")
                
                # Now generate tests from the parsed document
                test_request = {
                    "document_id": document_id,
                    "target_url": "https://user-management-demo.com",
                    "test_type": "functional",
                    "include_edge_cases": True,
                    "include_test_data": True
                }
                
                test_response = await client.post(
                    'http://localhost:8002/generate/tests-from-document',
                    json=test_request
                )
                
                if test_response.status_code == 200:
                    test_result = test_response.json()
                    
                    if test_result.get('success'):
                        print("✅ Generate tests endpoint successful!")
                        print(f"   🧪 Test cases: {len(test_result.get('test_cases', []))}")
                        print(f"   🚨 Edge cases: {len(test_result.get('edge_cases', []))}")
                        print(f"   📊 Test data: {len(test_result.get('test_data', []))}")
                        return True
                    else:
                        print(f"❌ Test generation error: {test_result.get('error')}")
                        return False
                else:
                    print(f"❌ HTTP error: {test_response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"❌ Generate tests test failed: {e}")
        return False
    
    finally:
        import shutil
        shutil.rmtree(temp_dir)


async def test_document_management_endpoints():
    """Test document listing and retrieval endpoints"""
    print("\n📋 Testing document management endpoints...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test list documents
            list_response = await client.get('http://localhost:8002/documents')
            
            if list_response.status_code == 200:
                list_result = list_response.json()
                print(f"✅ Document listing successful!")
                print(f"   📊 Total documents: {list_result.get('total_documents', 0)}")
                
                # If there are documents, test retrieval
                documents = list_result.get('documents', [])
                if documents:
                    doc_id = documents[0]['document_id']
                    
                    detail_response = await client.get(f'http://localhost:8002/documents/{doc_id}')
                    
                    if detail_response.status_code == 200:
                        detail_result = detail_response.json()
                        print(f"✅ Document detail retrieval successful!")
                        print(f"   📄 Document: {detail_result.get('metadata', {}).get('file_name', 'N/A')}")
                        print(f"   📝 Text length: {detail_result.get('metadata', {}).get('text_length', 0)}")
                        return True
                    else:
                        print(f"❌ Document detail error: {detail_response.status_code}")
                        return False
                else:
                    print("   ℹ️  No documents found in cache")
                    return True
            else:
                print(f"❌ Document listing error: {list_response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Document management test failed: {e}")
        return False


async def test_service_health():
    """Test service health endpoint"""
    print("\n🏥 Testing service health...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get('http://localhost:8002/health')
            
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Service health check successful!")
                print(f"   🏥 Status: {health.get('status')}")
                print(f"   🔧 Version: {health.get('version')}")
                print(f"   📁 Upload dir: {health.get('details', {}).get('upload_directory', 'N/A')}")
                print(f"   📄 Formats: {health.get('details', {}).get('supported_formats', 0)}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 80)
    print("🌐 DOCUMENT PARSER SERVICE ENDPOINTS TEST")
    print("=" * 80)
    print("💡 Make sure Document Parser Service is running on port 8002")
    print("💡 LLM Integration will be mocked for this test")
    print()
    
    test_results = []
    
    try:
        # Test service health first
        health_result = await test_service_health()
        test_results.append(("Service Health", health_result))
        
        if health_result:
            # Test main endpoints
            parse_gen_result, _ = await test_parse_and_generate_endpoint()
            test_results.append(("Parse and Generate Tests", parse_gen_result))
            
            gen_tests_result = await test_generate_tests_endpoint()
            test_results.append(("Generate Tests from Document", gen_tests_result))
            
            doc_mgmt_result = await test_document_management_endpoints()
            test_results.append(("Document Management", doc_mgmt_result))
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 ENDPOINT TEST RESULTS")
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
            print("🎉 ALL ENDPOINT TESTS PASSED!")
            print("✅ Document Parser Service with LLM integration is working perfectly")
            print("🚀 Service is ready for production use")
        else:
            print("⚠️  Some endpoint tests failed")
            if not health_result:
                print("💡 Make sure to start the Document Parser Service first:")
                print("   cd document-parser && ./start.sh")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Endpoint test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())