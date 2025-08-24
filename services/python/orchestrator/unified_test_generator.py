"""
Unified Test Generator - Combines Figma Design + Requirements Documents
Creates comprehensive test cases that merge UI components with business logic
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime
import httpx
import json

# Add shared modules to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

logger = structlog.get_logger()


class UnifiedTestGenerator:
    """
    Combines Figma design analysis with requirements documents 
    to create comprehensive, context-aware test cases
    """
    
    def __init__(
        self, 
        figma_service_url: str = "http://localhost:8001",
        document_service_url: str = "http://localhost:8002", 
        llm_service_url: str = "http://localhost:8005"
    ):
        self.figma_service_url = figma_service_url
        self.document_service_url = document_service_url
        self.llm_service_url = llm_service_url
        self.client = httpx.AsyncClient(timeout=300)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def generate_unified_test_suite(
        self,
        figma_file_key: str,
        requirements_document_path: str,
        target_url: str,
        project_name: str = "Unified Test Project"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive test suite combining Figma design + requirements
        
        This creates tests that understand BOTH:
        - What the UI looks like (from Figma)  
        - What the business logic should do (from requirements)
        """
        
        logger.info("Starting unified test generation",
                   figma_file=figma_file_key,
                   requirements_doc=requirements_document_path,
                   target_url=target_url)
        
        try:
            # Step 1: Analyze Figma design
            logger.info("Step 1: Analyzing Figma design components")
            figma_analysis = await self._analyze_figma_design(figma_file_key)
            
            if not figma_analysis["success"]:
                return {"success": False, "error": f"Figma analysis failed: {figma_analysis.get('error')}"}
            
            # Step 2: Parse requirements document  
            logger.info("Step 2: Parsing requirements document")
            requirements_analysis = await self._parse_requirements_document(requirements_document_path)
            
            if not requirements_analysis["success"]:
                return {"success": False, "error": f"Requirements parsing failed: {requirements_analysis.get('error')}"}
            
            # Step 3: Generate unified test cases using AI
            logger.info("Step 3: Generating unified test cases with AI")
            unified_tests = await self._generate_unified_tests_with_ai(
                figma_analysis["design_data"],
                requirements_analysis["requirements_data"], 
                target_url,
                project_name
            )
            
            if not unified_tests["success"]:
                return {"success": False, "error": f"Unified test generation failed: {unified_tests.get('error')}"}
            
            # Step 4: Enhance with cross-validation
            logger.info("Step 4: Adding design-requirement cross-validation")
            enhanced_tests = await self._add_design_requirement_validation(
                unified_tests["test_cases"],
                figma_analysis["design_data"],
                requirements_analysis["requirements_data"]
            )
            
            result = {
                "success": True,
                "project_name": project_name,
                "target_url": target_url,
                "generation_summary": {
                    "figma_components_analyzed": len(figma_analysis["design_data"].get("components", [])),
                    "requirements_sections_found": len(requirements_analysis["requirements_data"].get("sections", [])),
                    "unified_test_cases_generated": len(enhanced_tests),
                    "generation_approach": "figma_plus_requirements_unified"
                },
                "test_cases": enhanced_tests,
                "source_data": {
                    "figma_analysis": figma_analysis["design_data"],
                    "requirements_analysis": requirements_analysis["requirements_data"]
                }
            }
            
            logger.info("Unified test generation completed successfully",
                       figma_components=result["generation_summary"]["figma_components_analyzed"],
                       requirements_sections=result["generation_summary"]["requirements_sections_found"],
                       test_cases=result["generation_summary"]["unified_test_cases_generated"])
            
            return result
            
        except Exception as e:
            logger.error("Unified test generation failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _analyze_figma_design(self, figma_file_key: str) -> Dict[str, Any]:
        """Call Figma service to analyze design components"""
        try:
            response = await self.client.post(
                f"{self.figma_service_url}/analyze-figma-file",
                json={
                    "figma_file_key": figma_file_key,
                    "generate_tests": False,  # We'll generate unified tests instead
                    "extract_components": True,
                    "analyze_interactions": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "design_data": {
                        "components": data.get("components", []),
                        "frames": data.get("frames", []),
                        "interactions": data.get("interactions", []),
                        "design_system": data.get("design_system", {})
                    }
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Figma service request failed: {str(e)}"}
    
    async def _parse_requirements_document(self, document_path: str) -> Dict[str, Any]:
        """Call Document Parser service to extract requirements"""
        try:
            # Parse document
            with open(document_path, 'rb') as f:
                files = {'file': (os.path.basename(document_path), f, 'application/octet-stream')}
                
                response = await self.client.post(
                    f"{self.document_service_url}/parse/upload",
                    files=files
                )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Document parsing HTTP {response.status_code}: {response.text}"}
            
            parse_result = response.json()
            if not parse_result.get("success"):
                return {"success": False, "error": f"Document parsing failed: {parse_result.get('error')}"}
            
            # Extract requirements structure
            parsed_doc = parse_result["document"]
            
            return {
                "success": True,
                "requirements_data": {
                    "document_id": parsed_doc["id"],
                    "sections": parsed_doc["content"]["sections"],
                    "full_text": parsed_doc["content"]["text"],
                    "metadata": parsed_doc["content"]["metadata"],
                    "user_stories": self._extract_user_stories(parsed_doc["content"]["text"]),
                    "acceptance_criteria": self._extract_acceptance_criteria(parsed_doc["content"]["text"]),
                    "business_rules": self._extract_business_rules(parsed_doc["content"]["text"])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Requirements parsing failed: {str(e)}"}
    
    async def _generate_unified_tests_with_ai(
        self, 
        figma_data: Dict[str, Any], 
        requirements_data: Dict[str, Any],
        target_url: str,
        project_name: str
    ) -> Dict[str, Any]:
        """Use LLM to generate unified test cases that combine design + requirements"""
        
        try:
            # Build comprehensive context for AI
            context_prompt = self._build_unified_context_prompt(
                figma_data, requirements_data, target_url, project_name
            )
            
            # Call LLM service
            response = await self.client.post(
                f"{self.llm_service_url}/generate",
                json={
                    "provider": "openai",
                    "model": "gpt-4",
                    "prompt": context_prompt,
                    "context": {
                        "role": "Senior QA Engineer specialized in design-driven testing",
                        "task": "Generate comprehensive test cases that validate both UI design and business requirements",
                        "constraints": [
                            "Combine Figma design components with requirements context",
                            "Create end-to-end user journey tests",
                            "Include both visual validation and functional testing",
                            "Map UI components to business workflows"
                        ]
                    },
                    "max_tokens": 3000,
                    "temperature": 0.4
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"LLM service HTTP {response.status_code}: {response.text}"}
            
            llm_result = response.json()
            if not llm_result.get("success"):
                return {"success": False, "error": f"LLM generation failed: {llm_result.get('error')}"}
            
            # Parse LLM response into structured test cases
            test_cases = self._parse_unified_test_response(
                llm_result["content"], 
                figma_data, 
                requirements_data
            )
            
            return {
                "success": True,
                "test_cases": test_cases,
                "ai_response": llm_result["content"],
                "tokens_used": llm_result.get("tokens_used", 0)
            }
            
        except Exception as e:
            return {"success": False, "error": f"AI test generation failed: {str(e)}"}
    
    def _build_unified_context_prompt(
        self, 
        figma_data: Dict[str, Any], 
        requirements_data: Dict[str, Any],
        target_url: str,
        project_name: str
    ) -> str:
        """Build comprehensive prompt that combines Figma + requirements context"""
        
        # Extract Figma components summary
        components = figma_data.get("components", [])
        component_summary = []
        for comp in components[:10]:  # Limit to first 10 for prompt size
            component_summary.append(f"- {comp.get('name', 'Unknown')}: {comp.get('type', 'component')} at {comp.get('position', 'unknown position')}")
        
        # Extract requirements summary  
        user_stories = requirements_data.get("user_stories", [])
        acceptance_criteria = requirements_data.get("acceptance_criteria", [])
        
        prompt = f"""# Unified Test Case Generation: Design + Requirements

## Project Context
- **Project**: {project_name}
- **Target URL**: {target_url}
- **Approach**: Combine Figma design analysis with business requirements

## Figma Design Components Identified
{chr(10).join(component_summary)}

## Business Requirements Summary
### User Stories Found:
{chr(10).join([f"- {story}" for story in user_stories[:5]])}

### Key Acceptance Criteria:
{chr(10).join([f"- {criteria}" for criteria in acceptance_criteria[:5]])}

## Task: Generate Unified Test Cases

Create comprehensive test cases that:
1. **Validate UI Design**: Test actual Figma components and layout
2. **Verify Business Logic**: Ensure requirements are met
3. **End-to-End Workflows**: Complete user journeys from design to function
4. **Cross-Validation**: UI components support required business workflows

For each test case, include:
- **Test Name**: Descriptive name combining UI + business context
- **Business Context**: Which requirement/user story this validates
- **UI Components**: Specific Figma components being tested
- **Test Steps**: Step-by-step actions combining UI interaction + business validation
- **Expected Results**: Both visual and functional outcomes
- **Validation Points**: Design compliance + requirement fulfillment

Generate 5-8 comprehensive unified test cases in JSON format:
```json
[
  {{
    "name": "Complete User Registration Journey", 
    "business_context": "As a new user, I want to create an account...",
    "figma_components": ["RegisterForm", "SubmitButton", "SuccessMessage"],
    "test_type": "end_to_end_unified",
    "steps": [
      "Navigate to registration page and verify Figma 'RegisterForm' layout matches design",
      "Fill email field (Figma component 'EmailInput') with valid email",
      "Verify business rule: email validation per requirements",
      "Click 'Submit' button (Figma component 'PrimaryButton')",
      "Validate success message matches Figma 'SuccessMessage' design",
      "Verify business outcome: user account created as per requirements"
    ],
    "expected_results": [
      "UI matches Figma design specifications",
      "Business logic fulfills user story acceptance criteria",
      "End-to-end workflow completes successfully"
    ],
    "validation_points": [
      "Visual: Form layout matches Figma RegisterForm frame",
      "Functional: User registration meets acceptance criteria", 
      "Integration: UI components support business workflow"
    ]
  }}
]
```"""
        
        return prompt
    
    def _extract_user_stories(self, text: str) -> List[str]:
        """Extract user stories from requirements text"""
        import re
        
        # Look for "As a... I want... so that..." patterns
        user_story_patterns = [
            r"As a[^,]+,?\s+I want[^,]+,?\s+so that[^.]+",
            r"As an?[^,]+,?\s+I want[^,]+,?\s+so that[^.]+",
            r"User Story:?\s*(.+?)(?=\n\n|\n#|\nAcceptance|$)"
        ]
        
        stories = []
        for pattern in user_story_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            stories.extend([match.strip() for match in matches if match.strip()])
        
        return stories[:10]  # Limit to first 10
    
    def _extract_acceptance_criteria(self, text: str) -> List[str]:
        """Extract acceptance criteria from requirements text"""
        import re
        
        criteria_patterns = [
            r"Acceptance Criteria:?\s*\n?(.+?)(?=\n\n|\n#|\nUser Story|$)",
            r"Given[^,]+,?\s+when[^,]+,?\s+then[^.]+",
            r"- .+?(?=\n-|\n\n|\n#|$)"
        ]
        
        criteria = []
        for pattern in criteria_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, str):
                    # Split on newlines and clean up
                    lines = [line.strip() for line in match.split('\n') if line.strip()]
                    criteria.extend(lines)
        
        return criteria[:15]  # Limit to first 15
    
    def _extract_business_rules(self, text: str) -> List[str]:
        """Extract business rules from requirements text"""
        import re
        
        # Look for business rules, constraints, requirements
        business_patterns = [
            r"Business Rule:?\s*(.+?)(?=\n\n|\n#|$)",
            r"Constraint:?\s*(.+?)(?=\n\n|\n#|$)",
            r"System must[^.]+",
            r"Application should[^.]+",
            r"Users cannot[^.]+",
            r"The system shall[^.]+"
        ]
        
        rules = []
        for pattern in business_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rules.extend([match.strip() for match in matches if match.strip()])
        
        return rules[:10]  # Limit to first 10
    
    def _parse_unified_test_response(
        self, 
        ai_response: str, 
        figma_data: Dict[str, Any], 
        requirements_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse AI response into structured unified test cases"""
        
        try:
            import re
            
            # Try to extract JSON from AI response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                test_cases_data = json.loads(json_match.group())
            else:
                # Fallback: assume entire response is JSON
                test_cases_data = json.loads(ai_response)
            
            if not isinstance(test_cases_data, list):
                test_cases_data = [test_cases_data]
            
            # Enhance each test case with metadata
            enhanced_tests = []
            for test_data in test_cases_data:
                enhanced_test = {
                    "id": f"unified_{hash(test_data.get('name', 'test'))}",
                    "name": test_data.get("name", "Generated Unified Test"),
                    "description": test_data.get("business_context", ""),
                    "test_type": "unified_design_requirements",
                    "figma_components": test_data.get("figma_components", []),
                    "business_context": test_data.get("business_context", ""),
                    "steps": test_data.get("steps", []),
                    "expected_results": test_data.get("expected_results", []),
                    "validation_points": test_data.get("validation_points", []),
                    "priority": "high",  # Unified tests are high priority
                    "metadata": {
                        "generation_approach": "figma_plus_requirements",
                        "figma_components_count": len(test_data.get("figma_components", [])),
                        "has_business_context": bool(test_data.get("business_context")),
                        "validation_types": ["visual", "functional", "integration"]
                    }
                }
                enhanced_tests.append(enhanced_test)
            
            return enhanced_tests
            
        except Exception as e:
            logger.error("Failed to parse unified test response", error=str(e))
            return []
    
    async def _add_design_requirement_validation(
        self,
        test_cases: List[Dict[str, Any]],
        figma_data: Dict[str, Any],
        requirements_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Add cross-validation between design components and requirements"""
        
        enhanced_tests = []
        
        for test_case in test_cases:
            # Add design-requirement mapping validation
            figma_components = test_case.get("figma_components", [])
            business_context = test_case.get("business_context", "")
            
            # Add validation step for design-requirement alignment
            validation_steps = [
                f"🎨 DESIGN VALIDATION: Verify UI components {figma_components} are present and match Figma specifications",
                f"📋 REQUIREMENTS VALIDATION: Confirm test fulfills business requirement: '{business_context[:100]}...'",
                f"🔗 INTEGRATION VALIDATION: Ensure design components support required business workflow"
            ]
            
            # Enhance the test case
            enhanced_test = {
                **test_case,
                "design_requirement_validation": validation_steps,
                "traceability": {
                    "figma_components_mapped": figma_components,
                    "requirements_context": business_context,
                    "validation_approach": "unified_design_requirements"
                }
            }
            
            enhanced_tests.append(enhanced_test)
        
        return enhanced_tests