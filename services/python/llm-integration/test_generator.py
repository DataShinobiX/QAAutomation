"""
Intelligent Test Generator
Uses LLMs to generate, optimize, and analyze test cases
"""
import asyncio
import json
import structlog
from typing import Dict, List, Optional, Any

from config import LLMIntegrationConfig
from models import LLMRequest, LLMProvider, TestSuite, TestScenario, UITestCase
from llm_providers import LLMProviderManager
from prompt_manager import PromptManager
from utils import make_http_request, generate_id

logger = structlog.get_logger()


class IntelligentTestGenerator:
    """Generates intelligent tests using LLMs"""
    
    def __init__(self, config: LLMIntegrationConfig, llm_manager: LLMProviderManager):
        self.config = config
        self.llm_manager = llm_manager
        self.prompt_manager = PromptManager()
    
    async def generate_from_figma(
        self,
        figma_file_key: str,
        target_url: str,
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> TestSuite:
        """Generate intelligent tests from Figma design analysis"""
        logger.info("Generating intelligent tests from Figma",
                   figma_file_key=figma_file_key,
                   target_url=target_url)
        
        # Get Figma analysis from figma-service
        figma_response = await make_http_request(
            "GET",
            f"{self.config.figma_service_url}/figma/file/{figma_file_key}/analyze"
        )
        
        if not figma_response["success"]:
            raise Exception(f"Failed to get Figma analysis: {figma_response.get('error')}")
        
        figma_analysis = figma_response["data"]["analysis"]
        
        # Generate intelligent test scenarios using LLM
        test_scenarios = await self._generate_test_scenarios_from_design(
            figma_analysis, target_url, provider, model
        )
        
        # Generate UI-specific tests
        ui_tests = await self._generate_ui_tests_from_design(
            figma_analysis, target_url, provider, model
        )
        
        # Skip edge cases for minimal processing
        edge_cases = []
        
        # Convert Pydantic objects to dictionaries for API response
        ui_tests_dict = [test.dict() for test in ui_tests]
        scenarios_dict = [scenario.dict() for scenario in (test_scenarios + edge_cases)]
        
        test_suite = TestSuite(
            name=f"AI-Generated Tests - {figma_analysis.get('name', 'Figma Design')}",
            description=f"Intelligent tests generated from Figma design analysis using {provider}",
            url=target_url,
            figma_file_key=figma_file_key,
            ui_tests=ui_tests_dict,
            scenarios=scenarios_dict
        )
        
        logger.info("Generated intelligent test suite from Figma",
                   ui_tests=len(ui_tests),
                   scenarios=len(test_scenarios),
                   edge_cases=len(edge_cases))
        
        return test_suite
    
    async def generate_from_requirements(
        self,
        requirements_text: str,
        target_url: str,
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> TestSuite:
        """Generate tests from requirements/user stories"""
        logger.info("Generating tests from requirements",
                   requirements_length=len(requirements_text),
                   target_url=target_url)
        
        # Parse requirements into structured format
        parsed_requirements = await self._parse_requirements(
            requirements_text, provider, model
        )
        
        # Generate test scenarios for each requirement
        test_scenarios = []
        for requirement in parsed_requirements:
            scenarios = await self._generate_scenarios_from_requirement(
                requirement, target_url, provider, model
            )
            test_scenarios.extend(scenarios)
        
        # Generate acceptance criteria tests
        acceptance_tests = await self._generate_acceptance_tests(
            parsed_requirements, target_url, provider, model
        )
        
        test_suite = TestSuite(
            name=f"AI-Generated Tests - Requirements",
            description=f"Intelligent tests generated from requirements using {provider}",
            url=target_url,
            scenarios=test_scenarios + acceptance_tests
        )
        
        logger.info("Generated test suite from requirements",
                   scenarios=len(test_scenarios),
                   acceptance_tests=len(acceptance_tests))
        
        return test_suite
    
    async def optimize_test_suite(
        self,
        test_suite_data: dict,
        optimization_goals: List[str],
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> dict:
        """Optimize existing test suite using AI"""
        logger.info("Optimizing test suite with AI",
                   test_count=len(test_suite_data.get("ui_tests", [])),
                   goals=optimization_goals)
        
        # Analyze current test suite
        analysis = await self._analyze_test_suite(test_suite_data, provider, model)
        
        # Generate optimization recommendations
        recommendations = await self._generate_optimization_recommendations(
            test_suite_data, analysis, optimization_goals, provider, model
        )
        
        # Apply optimizations
        optimized_suite = await self._apply_optimizations(
            test_suite_data, recommendations, provider, model
        )
        
        return {
            "original_suite": test_suite_data,
            "analysis": analysis,
            "recommendations": recommendations,
            "optimized_suite": optimized_suite,
            "optimization_summary": {
                "original_test_count": len(test_suite_data.get("ui_tests", [])),
                "optimized_test_count": len(optimized_suite.get("ui_tests", [])),
                "goals_addressed": optimization_goals
            }
        }
    
    async def generate_edge_cases(
        self,
        feature_description: str,
        existing_tests: List[dict],
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> List[TestScenario]:
        """Generate edge case test scenarios"""
        logger.info("Generating edge cases",
                   feature_description=feature_description[:100],
                   existing_test_count=len(existing_tests))
        
        prompt = await self.prompt_manager.get_prompt(
            "edge_case_generation",
            {
                "feature_description": feature_description,
                "existing_tests": json.dumps(existing_tests, indent=2),
                "test_count": min(10, max(3, len(existing_tests) // 2))
            }
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
            context={
                "role": "QA Engineer specializing in edge case testing",
                "task": "Generate comprehensive edge case scenarios",
                "format": "JSON array of test scenarios"
            }
        )
        
        response = await self.llm_manager.generate_text(request)
        edge_cases_data = self._parse_llm_json_response(response.content)
        
        edge_cases = []
        for case_data in edge_cases_data:
            edge_case = TestScenario(
                name=case_data.get("name", "Generated Edge Case"),
                description=case_data.get("description", ""),
                steps=case_data.get("steps", []),
                expected_result=case_data.get("expected_result", ""),
                test_type="edge_case",
                priority="medium"
            )
            edge_cases.append(edge_case)
        
        logger.info("Generated edge cases", count=len(edge_cases))
        return edge_cases
    
    async def analyze_test_results(
        self,
        test_results: dict,
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> dict:
        """Analyze test execution results and provide insights"""
        logger.info("Analyzing test results with AI",
                   total_tests=test_results.get("total_tests", 0),
                   failed_tests=test_results.get("failed_tests", 0))
        
        prompt = await self.prompt_manager.get_prompt(
            "test_result_analysis",
            {
                "test_results": json.dumps(test_results, indent=2),
                "failure_rate": (test_results.get("failed_tests", 0) / 
                               max(1, test_results.get("total_tests", 1))) * 100
            }
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3,
            context={
                "role": "Senior QA Analyst",
                "task": "Analyze test results and provide actionable insights",
                "format": "Structured analysis with recommendations"
            }
        )
        
        response = await self.llm_manager.generate_text(request)
        
        try:
            analysis = self._parse_llm_json_response(response.content)
        except:
            # Fallback to text analysis if JSON parsing fails
            analysis = {
                "summary": response.content,
                "insights": [],
                "recommendations": [],
                "risk_assessment": "medium"
            }
        
        return analysis
    
    async def generate_bug_reproduction_steps(
        self,
        bug_description: str,
        error_logs: str = "",
        screenshot_analysis: dict = None,
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> dict:
        """Generate detailed bug reproduction steps"""
        logger.info("Generating bug reproduction steps",
                   bug_description=bug_description[:100],
                   has_logs=bool(error_logs),
                   has_screenshot=bool(screenshot_analysis))
        
        context_data = {
            "bug_description": bug_description,
            "error_logs": error_logs[:2000] if error_logs else "No logs provided",
            "screenshot_info": json.dumps(screenshot_analysis) if screenshot_analysis else "No screenshot analysis"
        }
        
        prompt = await self.prompt_manager.get_prompt(
            "bug_reproduction",
            context_data
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2,
            context={
                "role": "Bug reproduction specialist",
                "task": "Create detailed reproduction steps",
                "format": "Structured steps with environment details"
            }
        )
        
        response = await self.llm_manager.generate_text(request)
        
        try:
            reproduction_data = self._parse_llm_json_response(response.content)
        except:
            # Fallback format
            reproduction_data = {
                "steps": response.content.split("\n"),
                "environment": "Not specified",
                "severity": "medium",
                "category": "functional"
            }
        
        return reproduction_data
    
    # Private helper methods
    
    async def _generate_test_scenarios_from_design(
        self,
        figma_analysis: dict,
        target_url: str,
        provider: str,
        model: str
    ) -> List[TestScenario]:
        """Generate test scenarios from Figma design"""
        frames = figma_analysis.get("frames", [])
        if not frames:
            return []
        
        # Process only 1 frame and 1 component to minimize token usage
        if not frames:
            return []
        
        first_frame = frames[0]
        components = first_frame.get("components", [])
        
        if not components:
            return []
        
        # Use only the first component for minimal processing
        first_component = components[0]
        
        # Create minimal component summary
        component_summary = {
            "frame_name": first_frame.get("name", "Main Frame"),
            "component": {
                "name": first_component.get("name", "Unknown Component"),
                "type": first_component.get("type", "Unknown"),
                "has_text": bool(first_component.get("characters")),
                "is_interactive": any(keyword in first_component.get("name", "").lower() 
                                   for keyword in ["button", "input", "link", "field", "form"])
            },
            "design_context": {
                "design_name": figma_analysis.get("name", "Design"),
                "target_url": target_url,
                "total_frames": len(frames),
                "total_components": len(components)
            }
        }
        
        prompt = await self.prompt_manager.get_prompt(
            "figma_minimal_scenario_generation",
            component_summary
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=500,  # Reduced for faster processing
            temperature=0.3  # Lower temperature for more focused output
        )
        
        response = await self.llm_manager.generate_text(request)
        scenarios_data = self._parse_llm_json_response(response.content)
        
        scenarios = []
        for scenario_data in scenarios_data:
            scenario = TestScenario(
                name=scenario_data.get("name", "Generated Scenario"),
                description=scenario_data.get("description", ""),
                steps=scenario_data.get("steps", []),
                expected_result=scenario_data.get("expected_result", ""),
                test_type="functional",
                priority=scenario_data.get("priority", "medium")
            )
            scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_ui_tests_from_design(
        self,
        figma_analysis: dict,
        target_url: str,
        provider: str,
        model: str
    ) -> List[UITestCase]:
        """Generate UI tests from design components"""
        frames = figma_analysis.get("frames", [])
        if not frames:
            return []
        
        # Use only 1 component for minimal UI test generation
        first_frame = frames[0]
        components = first_frame.get("components", [])
        
        if not components:
            return []
        
        # Process only the first component
        first_component = components[0]
        
        # Create minimal component data for UI test generation
        minimal_component = {
            "name": first_component.get("name", "Unknown"),
            "type": first_component.get("type", "Unknown"),
            "has_text": bool(first_component.get("characters")),
            "text_content": first_component.get("characters", "")[:100] if first_component.get("characters") else "",
            "is_interactive": any(keyword in first_component.get("name", "").lower() 
                               for keyword in ["button", "input", "link", "field", "form"])
        }
        
        prompt = await self.prompt_manager.get_prompt(
            "ui_test_minimal_generation",
            {
                "component": minimal_component,
                "frame_name": first_frame.get("name", "Main Frame"),
                "target_url": target_url
            }
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=300,  # Minimal tokens for single component
            temperature=0.2  # Very focused output
        )
        
        response = await self.llm_manager.generate_text(request)
        ui_tests_data = self._parse_llm_json_response(response.content)
        
        ui_tests = []
        for test_data in ui_tests_data:
            # Fix expected_value to always be string or None
            expected_value = test_data.get("expected_value")
            if expected_value is not None:
                expected_value = str(expected_value)
                
            ui_test = UITestCase(
                component_name=test_data.get("component_name", "Generated Component"),
                selector=test_data.get("selector", "*"),
                test_type=test_data.get("test_type", "exists"),
                expected_value=expected_value
            )
            ui_tests.append(ui_test)
        
        return ui_tests
    
    async def _generate_edge_cases_from_design(
        self,
        figma_analysis: dict,
        provider: str,
        model: str
    ) -> List[TestScenario]:
        """Generate edge cases based on design analysis"""
        # Analyze design for potential edge cases
        prompt = await self.prompt_manager.get_prompt(
            "design_edge_cases",
            {
                "design_summary": str(figma_analysis)[:1000],  # Limit context
                "frame_count": len(figma_analysis.get("frames", []))
            }
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7
        )
        
        response = await self.llm_manager.generate_text(request)
        edge_cases_data = self._parse_llm_json_response(response.content)
        
        edge_cases = []
        for case_data in edge_cases_data:
            edge_case = TestScenario(
                name=case_data.get("name", "Edge Case"),
                description=case_data.get("description", ""),
                steps=case_data.get("steps", []),
                expected_result=case_data.get("expected_result", ""),
                test_type="edge_case",
                priority="low"
            )
            edge_cases.append(edge_case)
        
        return edge_cases
    
    async def _parse_requirements(
        self,
        requirements_text: str,
        provider: str,
        model: str
    ) -> List[dict]:
        """Parse requirements text into structured format"""
        prompt = await self.prompt_manager.get_prompt(
            "requirement_parsing",
            {
                "requirements_text": requirements_text[:3000],  # Limit length
            }
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=1500,
            temperature=0.2
        )
        
        response = await self.llm_manager.generate_text(request)
        return self._parse_llm_json_response(response.content)
    
    def _parse_llm_json_response(self, content: str) -> Any:
        """Parse LLM response as JSON with fallback"""
        try:
            # Try to find JSON in the response
            content = content.strip()
            
            # Look for JSON blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON", content=content[:100])
            # Return empty list as fallback
            return []
    
    async def _generate_scenarios_from_requirement(
        self,
        requirement: dict,
        target_url: str,
        provider: str,
        model: str
    ) -> List[TestScenario]:
        """Generate test scenarios from a single requirement"""
        prompt = await self.prompt_manager.get_prompt(
            "requirement_scenarios",
            {
                "requirement": json.dumps(requirement, indent=2),
                "target_url": target_url
            }
        )
        
        request = LLMRequest(
            provider=LLMProvider(provider),
            model=model,
            prompt=prompt,
            max_tokens=1000,
            temperature=0.5
        )
        
        response = await self.llm_manager.generate_text(request)
        scenarios_data = self._parse_llm_json_response(response.content)
        
        scenarios = []
        for scenario_data in scenarios_data:
            scenario = TestScenario(
                name=scenario_data.get("name", "Generated Scenario"),
                description=scenario_data.get("description", ""),
                steps=scenario_data.get("steps", []),
                expected_result=scenario_data.get("expected_result", ""),
                test_type="functional",
                source_story=requirement.get("id")
            )
            scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_acceptance_tests(
        self,
        requirements: List[dict],
        target_url: str,
        provider: str,
        model: str
    ) -> List[TestScenario]:
        """Generate acceptance tests from requirements"""
        # Implementation for acceptance test generation
        # Similar pattern to other generation methods
        return []
    
    async def _analyze_test_suite(
        self,
        test_suite_data: dict,
        provider: str,
        model: str
    ) -> dict:
        """Analyze test suite for optimization opportunities"""
        # Implementation for test suite analysis
        return {"analysis": "placeholder"}
    
    async def _generate_optimization_recommendations(
        self,
        test_suite_data: dict,
        analysis: dict,
        goals: List[str],
        provider: str,
        model: str
    ) -> List[dict]:
        """Generate optimization recommendations"""
        # Implementation for optimization recommendations
        return []
    
    async def _apply_optimizations(
        self,
        test_suite_data: dict,
        recommendations: List[dict],
        provider: str,
        model: str
    ) -> dict:
        """Apply optimizations to test suite"""
        # Implementation for applying optimizations
        return test_suite_data