#!/usr/bin/env python3
"""
End-to-End Integrated Workflow Test
Demonstrates complete QA automation platform integration
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class IntegratedWorkflowTester:
    """Tests the complete integrated QA automation workflow"""
    
    def __init__(self):
        self.services = {
            # Rust Performance Services
            "website_analyzer": "http://localhost:3001",
            "visual_engine": "http://localhost:3002", 
            "test_executor": "http://localhost:3003",
            
            # Python AI Services
            "figma_service": "http://localhost:8001",
            "document_parser": "http://localhost:8002",
            "nlp_service": "http://localhost:8003",
            "computer_vision": "http://localhost:8004",
            "llm_integration": "http://localhost:8005",
            "orchestrator": "http://localhost:8006",
            "auth_manager": "http://localhost:8007",
            "workflow_orchestrator": "http://localhost:8008"
        }
        
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def check_service_health(self) -> Dict[str, bool]:
        """Check health of all services"""
        print("🔍 Checking service health...")
        
        health_status = {}
        
        for service_name, base_url in self.services.items():
            try:
                response = await self.client.get(f"{base_url}/health", timeout=5.0)
                health_status[service_name] = response.status_code == 200
                
                if health_status[service_name]:
                    print(f"  ✅ {service_name}: Healthy")
                else:
                    print(f"  ❌ {service_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                health_status[service_name] = False
                print(f"  ❌ {service_name}: {str(e)[:50]}...")
        
        healthy_count = sum(health_status.values())
        total_count = len(health_status)
        
        print(f"\n📊 Service Health Summary: {healthy_count}/{total_count} services healthy")
        
        return health_status
    
    async def test_authentication_service(self) -> Dict[str, Any]:
        """Test authentication service with a demo site"""
        print("\n🔐 Testing Authentication Service...")
        
        try:
            # Test connection check first
            test_url = "https://httpbin.org/forms/post"  # Form example
            
            response = await self.client.post(
                f"{self.services['auth_manager']}/test-connection",
                params={"url": test_url}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Connection test successful")
                print(f"     - Accessible: {result.get('accessible')}")
                print(f"     - Requires Auth: {result.get('requires_authentication')}")
                print(f"     - Status Code: {result.get('status_code')}")
                
                return {"success": True, "connection_test": result}
            else:
                print(f"  ❌ Connection test failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Authentication service test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_website_analyzer(self) -> Dict[str, Any]:
        """Test website analyzer service"""
        print("\n🌐 Testing Website Analyzer...")
        
        try:
            test_url = "https://httpbin.org"
            
            response = await self.client.post(
                f"{self.services['website_analyzer']}/analyze",
                json={"url": test_url}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Website analysis successful")
                print(f"     - URL: {test_url}")
                print(f"     - Elements found: {len(result.get('elements', []))}")
                print(f"     - Links found: {len(result.get('links', []))}")
                
                return {"success": True, "analysis": result}
            else:
                print(f"  ❌ Website analysis failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Website analyzer test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_document_parser(self) -> Dict[str, Any]:
        """Test document parser service"""
        print("\n📄 Testing Document Parser...")
        
        try:
            # Create a sample requirements document
            sample_requirements = """
            # Sample Web Application Requirements
            
            ## User Authentication
            - Users must be able to login with email and password
            - System should support password reset functionality
            - Failed login attempts should be logged
            
            ## Dashboard Features  
            - Authenticated users should see a dashboard
            - Dashboard should display user profile information
            - Users should be able to update their profile
            
            ## Security Requirements
            - All forms must include CSRF protection
            - Passwords must be at least 8 characters
            - Session timeout after 30 minutes of inactivity
            """
            
            # Save to temporary file
            temp_file = "/tmp/sample_requirements.md"
            with open(temp_file, "w") as f:
                f.write(sample_requirements)
            
            response = await self.client.post(
                f"{self.services['document_parser']}/parse/file",
                json={"file_path": temp_file}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Document parsing successful")
                print(f"     - Sections found: {len(result.get('sections', []))}")
                print(f"     - Requirements extracted: {len(result.get('content', '').split('- ')) - 1}")
                
                return {"success": True, "parsing": result}
            else:
                print(f"  ❌ Document parsing failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Document parser test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_unified_orchestrator(self) -> Dict[str, Any]:
        """Test the unified test generation"""
        print("\n🎯 Testing Unified Test Orchestrator...")
        
        try:
            # Create test requirements file
            sample_requirements = {
                "content": """
                # E-commerce Application Testing Requirements
                
                ## Login Functionality
                - Users should be able to login with valid credentials
                - Invalid login attempts should show error messages
                - Password reset should be available
                
                ## Product Catalog
                - Products should be displayed in a grid layout
                - Users should be able to filter products by category
                - Product details should be accessible via click
                
                ## Shopping Cart
                - Users should be able to add products to cart
                - Cart should persist across sessions
                - Checkout process should be secure
                """,
                "file_type": "markdown"
            }
            
            response = await self.client.post(
                f"{self.services['orchestrator']}/generate-unified-tests",
                json={
                    "target_url": "https://httpbin.org",
                    "requirements_data": sample_requirements,
                    "project_name": "E2E Integration Test"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Unified test generation successful")
                print(f"     - Test scenarios: {len(result.get('test_scenarios', []))}")
                print(f"     - Test categories: {len(result.get('test_categories', {}))}")
                
                return {"success": True, "unified_tests": result}
            else:
                print(f"  ❌ Unified test generation failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Unified orchestrator test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_integrated_workflow(self) -> Dict[str, Any]:
        """Test the complete integrated workflow"""
        print("\n🚀 Testing Complete Integrated Workflow...")
        
        try:
            # Start an integrated workflow
            workflow_request = {
                "url": "https://httpbin.org",
                "workflow_type": "full_analysis",
                "requirements_data": {
                    "content": """
                    # Test Application Requirements
                    
                    ## Core Functionality
                    - Application should be accessible via web browser
                    - Homepage should load within 3 seconds
                    - Navigation should be intuitive and responsive
                    
                    ## API Testing
                    - REST endpoints should return proper HTTP status codes
                    - JSON responses should be well-formatted
                    - Error handling should be graceful
                    """,
                    "file_type": "markdown"
                }
            }
            
            # Start workflow
            response = await self.client.post(
                f"{self.services['workflow_orchestrator']}/workflows/start",
                json=workflow_request
            )
            
            if response.status_code == 200:
                workflow_result = response.json()
                workflow_id = workflow_result.get("workflow_id")
                
                print(f"  ✅ Workflow started successfully")
                print(f"     - Workflow ID: {workflow_id}")
                print(f"     - Status: {workflow_result.get('status')}")
                
                # Monitor workflow progress
                max_wait_time = 120  # 2 minutes
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    status_response = await self.client.get(
                        f"{self.services['workflow_orchestrator']}/workflows/{workflow_id}/status"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status")
                        progress = status_data.get("progress", 0)
                        current_step = status_data.get("current_step", "")
                        
                        print(f"     - Progress: {progress:.1f}% - {current_step}")
                        
                        if status in ["completed", "failed"]:
                            # Get final results
                            results_response = await self.client.get(
                                f"{self.services['workflow_orchestrator']}/workflows/{workflow_id}/results"
                            )
                            
                            if results_response.status_code == 200:
                                final_results = results_response.json()
                                
                                if status == "completed":
                                    print(f"  ✅ Integrated workflow completed successfully!")
                                    print(f"     - Execution time: {final_results.get('execution_time', 0):.2f}s")
                                    
                                    # Print summary of results
                                    results = final_results.get("results", {}).get("workflow_results", {})
                                    for step_name, step_result in results.items():
                                        success_status = "✅" if step_result.get("success") else "❌"
                                        print(f"     - {step_name}: {success_status}")
                                    
                                    return {"success": True, "workflow_results": final_results}
                                else:
                                    print(f"  ❌ Integrated workflow failed")
                                    errors = final_results.get("results", {}).get("errors", [])
                                    for error in errors:
                                        print(f"     - Error: {error}")
                                    
                                    return {"success": False, "errors": errors}
                            
                            break
                    
                    await asyncio.sleep(5)  # Check every 5 seconds
                
                print(f"  ⚠️ Workflow monitoring timeout after {max_wait_time}s")
                return {"success": False, "error": "Workflow monitoring timeout"}
                
            else:
                print(f"  ❌ Failed to start integrated workflow: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Integrated workflow test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_service_integration_status(self) -> Dict[str, Any]:
        """Test service integration status endpoint"""
        print("\n📊 Testing Service Integration Status...")
        
        try:
            response = await self.client.get(
                f"{self.services['workflow_orchestrator']}/service-status"
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("summary", {})
                
                print(f"  ✅ Service integration status retrieved")
                print(f"     - Total services: {summary.get('total_services')}")
                print(f"     - Healthy services: {summary.get('healthy_services')}")
                print(f"     - Unhealthy services: {summary.get('unhealthy_services')}")
                
                # Show detailed status
                services = result.get("services", {})
                for service_name, service_status in services.items():
                    health_icon = "✅" if service_status.get("healthy") else "❌"
                    response_time = service_status.get("response_time_ms")
                    time_str = f"({response_time:.1f}ms)" if response_time else ""
                    print(f"     - {service_name}: {health_icon} {time_str}")
                
                return {"success": True, "integration_status": result}
            else:
                print(f"  ❌ Service integration status failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ❌ Service integration status test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete integration test suite"""
        print("🎉 Starting Complete QA Automation Platform Integration Test")
        print("=" * 80)
        
        start_time = datetime.utcnow()
        test_results = {}
        
        # 1. Check service health
        health_status = await self.check_service_health()
        test_results["service_health"] = health_status
        
        # Count healthy services
        healthy_services = sum(health_status.values())
        total_services = len(health_status)
        
        if healthy_services < total_services * 0.7:  # At least 70% services should be healthy
            print(f"\n⚠️ Warning: Only {healthy_services}/{total_services} services are healthy")
            print("Some tests may fail due to unavailable services.")
        
        # 2. Test individual services
        test_results["authentication"] = await self.test_authentication_service()
        test_results["website_analysis"] = await self.test_website_analyzer()
        test_results["document_parsing"] = await self.test_document_parser()
        test_results["unified_orchestration"] = await self.test_unified_orchestrator()
        
        # 3. Test service integration
        test_results["service_integration"] = await self.test_service_integration_status()
        
        # 4. Test complete integrated workflow
        test_results["integrated_workflow"] = await self.test_integrated_workflow()
        
        # Calculate results
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Count successful tests
        successful_tests = sum(1 for result in test_results.values() 
                             if isinstance(result, dict) and result.get("success", False))
        total_tests = len([r for r in test_results.values() if isinstance(r, dict)])
        
        print("\n" + "=" * 80)
        print("🎯 INTEGRATION TEST RESULTS SUMMARY")
        print("=" * 80)
        
        print(f"📊 Overall Results:")
        print(f"   - Services Health: {healthy_services}/{total_services} services healthy")
        print(f"   - Test Results: {successful_tests}/{total_tests} tests passed")
        print(f"   - Execution Time: {execution_time:.2f} seconds")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in test_results.items():
            if isinstance(result, dict):
                status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
                print(f"   - {test_name.replace('_', ' ').title()}: {status}")
                if not result.get("success") and result.get("error"):
                    print(f"     Error: {result['error']}")
        
        # Overall success assessment
        overall_success = (
            healthy_services >= total_services * 0.7 and  # At least 70% services healthy
            successful_tests >= total_tests * 0.8  # At least 80% tests passed
        )
        
        if overall_success:
            print(f"\n🎉 INTEGRATION TEST SUITE: ✅ OVERALL SUCCESS")
            print(f"   The QA Automation Platform integration is working correctly!")
        else:
            print(f"\n⚠️ INTEGRATION TEST SUITE: ❌ NEEDS ATTENTION") 
            print(f"   Some services or integration tests failed. Please check the logs.")
        
        print(f"\n💡 Next Steps:")
        if overall_success:
            print(f"   - Platform is ready for production workflows")
            print(f"   - All major integration points are functional")
            print(f"   - Services are communicating properly")
        else:
            print(f"   - Review failed services and restart them if needed")
            print(f"   - Check network connectivity between services")
            print(f"   - Verify service configurations and dependencies")
        
        return {
            "overall_success": overall_success,
            "execution_time": execution_time,
            "service_health": f"{healthy_services}/{total_services}",
            "test_results": f"{successful_tests}/{total_tests}",
            "detailed_results": test_results
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def main():
    """Main test execution function"""
    tester = IntegratedWorkflowTester()
    
    try:
        results = await tester.run_complete_test_suite()
        
        # Return appropriate exit code
        exit_code = 0 if results["overall_success"] else 1
        return exit_code
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test suite interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")
        return 1
    finally:
        await tester.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)