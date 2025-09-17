#!/usr/bin/env python3
"""
Test the complete QA workflow end-to-end
"""
import asyncio
import sys
import os
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'python', 'shared'))

async def test_complete_workflow():
    """Test the complete integrated workflow"""
    
    print("🚀 TESTING COMPLETE QA WORKFLOW")
    print("=" * 60)
    
    try:
        from service_integration import ServiceIntegrator, IntegrationRequest
        
        integrator = ServiceIntegrator()
        
        # Create integration request
        request = IntegrationRequest(
            url="https://demo.validdo.com/signup",
            figma_file_key="SL2zhCoS31dtNI5YRwti2F",
            workflow_type="full_analysis"
        )
        
        print(f"Target URL: {request.url}")
        print(f"Figma File Key: {request.figma_file_key}")
        print(f"Workflow Type: {request.workflow_type}")
        print()
        
        print("Starting integrated workflow...")
        result = await integrator.run_integrated_workflow(request)
        
        print(f"Workflow ID: {result.workflow_id}")
        print(f"Success: {result.success}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"Errors: {len(result.errors)}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
        
        print(f"\nService Statuses:")
        for service, status in result.service_statuses.items():
            status_emoji = "✅" if status else "❌"
            print(f"  {status_emoji} {service}: {'healthy' if status else 'unhealthy'}")
        
        print(f"\nWorkflow Results:")
        for step, step_result in result.results.items():
            if isinstance(step_result, dict):
                success = step_result.get('success', False)
                status_emoji = "✅" if success else "❌"
                print(f"  {status_emoji} {step}: {'completed' if success else 'failed'}")
                
                # Special handling for test execution results
                if step == "test_execution" and success:
                    execution = step_result.get("data", {}).get("execution", {})
                    print(f"      Tests: {execution.get('total_tests', 0)} total, "
                          f"{execution.get('passed_tests', 0)} passed, "
                          f"{execution.get('failed_tests', 0)} failed")
                elif step == "unified_tests" and success:
                    test_suite = step_result.get("data", {}).get("test_suite", {})
                    test_count = len(test_suite.get("test_cases", test_suite.get("ui_tests", [])))
                    print(f"      Generated {test_count} test cases")
        
        # Show final report if available
        if "final_report" in result.results:
            report = result.results["final_report"]
            if report.get("success"):
                report_data = report.get("report", {})
                summary = report_data.get("summary", {})
                print(f"\n📊 FINAL REPORT:")
                print(f"  Workflow Success: {summary.get('workflow_success')}")
                print(f"  Services Used: {summary.get('total_services_used')}")
                print(f"  Tests Executed: {summary.get('tests_executed')}")
                print(f"  AI Insights Available: {summary.get('ai_insights_available')}")
                
                quality_metrics = report_data.get("quality_metrics", {})
                print(f"\n🎯 QUALITY METRICS:")
                print(f"  Test Pass Rate: {quality_metrics.get('test_pass_rate', 0):.1f}%")
                print(f"  Overall Quality Score: {quality_metrics.get('overall_quality_score', 0):.1f}")
        
        print(f"\n{'✅ WORKFLOW COMPLETED SUCCESSFULLY' if result.success else '❌ WORKFLOW COMPLETED WITH ERRORS'}")
        
        await integrator.close()
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())