"""
LLM Integration for Document Parser Service
Converts parsed documents into test cases using AI
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

from doc_parser_config import config

try:
    from models import ParsedDocument, DocumentContent, TestScenario, UITestCase
except ImportError:
    from parser_manager import ParsedDocument
    from document_parsers import DocumentContent
    
    # Fallback models
    from pydantic import BaseModel, Field
    from typing import List, Optional
    from datetime import datetime
    import uuid
    
    class TestScenario(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        name: str
        description: str
        steps: List[str]
        expected_outcome: str
        priority: str = "medium"
        test_type: str = "functional"
        metadata: Dict[str, Any] = {}
    
    class UITestCase(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        name: str
        description: str
        scenarios: List[TestScenario] = []
        target_url: Optional[str] = None
        generated_at: datetime = Field(default_factory=datetime.utcnow)
        metadata: Dict[str, Any] = {}

logger = structlog.get_logger()


class DocumentToTestConverter:
    """Converts parsed documents to test cases using LLM Integration Service"""
    
    def __init__(self, llm_service_url: str = "http://localhost:8005"):
        self.llm_service_url = llm_service_url
        self.client = httpx.AsyncClient(timeout=300)  # 5 minute timeout
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def convert_requirements_to_tests(
        self, 
        parsed_doc: ParsedDocument, 
        target_url: Optional[str] = None,
        test_type: str = "functional"
    ) -> Dict[str, Any]:
        """Convert requirements document to test cases"""
        
        logger.info("Converting requirements document to tests",
                   doc_id=parsed_doc.id,
                   source_type=parsed_doc.source_type,
                   target_url=target_url)
        
        # Extract key requirements from parsed document
        requirements_text = self._extract_requirements(parsed_doc)
        
        if not requirements_text:
            return {
                "success": False,
                "error": "No requirements found in document",
                "test_cases": []
            }
        
        try:
            # Generate test scenarios using LLM service
            llm_response = await self._call_llm_service({
                "provider": "openai",
                "model": "gpt-4",
                "prompt": self._build_requirements_prompt(requirements_text, target_url),
                "context": {
                    "role": "Senior QA Engineer",
                    "task": "Convert requirements into comprehensive test scenarios",
                    "format": "JSON with test scenarios and steps",
                    "constraints": [
                        "Focus on user acceptance criteria",
                        "Include both positive and negative test cases",
                        "Make test steps specific and actionable",
                        "Consider edge cases and error conditions"
                    ]
                },
                "max_tokens": 2000,
                "temperature": 0.3
            })
            
            if not llm_response.get("success"):
                return {
                    "success": False,
                    "error": f"LLM service error: {llm_response.get('error')}",
                    "test_cases": []
                }
            
            # Parse LLM response into structured test cases
            test_cases = self._parse_llm_test_response(
                llm_response["content"], 
                parsed_doc,
                target_url
            )
            
            logger.info("Requirements converted to tests successfully",
                       doc_id=parsed_doc.id,
                       test_count=len(test_cases))
            
            return {
                "success": True,
                "test_cases": test_cases,
                "source_document": {
                    "id": parsed_doc.id,
                    "file_name": parsed_doc.content.metadata.file_name if parsed_doc.content.metadata else "unknown",
                    "requirements_count": len(requirements_text.split('\n')),
                    "processing_time": parsed_doc.processing_time
                }
            }
            
        except Exception as e:
            logger.error("Requirements to tests conversion failed",
                        doc_id=parsed_doc.id,
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "test_cases": []
            }
    
    async def generate_edge_cases_from_document(
        self,
        parsed_doc: ParsedDocument,
        existing_tests: List[TestScenario] = None
    ) -> Dict[str, Any]:
        """Generate edge cases based on document content"""
        
        logger.info("Generating edge cases from document",
                   doc_id=parsed_doc.id)
        
        try:
            # Extract feature descriptions from document
            features = self._extract_features(parsed_doc)
            
            existing_test_names = [test.name for test in (existing_tests or [])]
            
            # Generate edge cases using LLM
            llm_response = await self._call_llm_service({
                "provider": "openai",
                "model": "gpt-4",
                "prompt": self._build_edge_case_prompt(features, existing_test_names),
                "context": {
                    "role": "Senior QA Engineer specialized in edge case testing",
                    "task": "Generate comprehensive edge cases and negative scenarios",
                    "format": "JSON with detailed test scenarios"
                },
                "max_tokens": 1500,
                "temperature": 0.7
            })
            
            if not llm_response.get("success"):
                return {
                    "success": False,
                    "error": f"LLM service error: {llm_response.get('error')}",
                    "edge_cases": []
                }
            
            edge_cases = self._parse_edge_case_response(
                llm_response["content"],
                parsed_doc
            )
            
            logger.info("Edge cases generated successfully",
                       doc_id=parsed_doc.id,
                       edge_case_count=len(edge_cases))
            
            return {
                "success": True,
                "edge_cases": edge_cases,
                "source_document": {
                    "id": parsed_doc.id,
                    "features_extracted": len(features)
                }
            }
            
        except Exception as e:
            logger.error("Edge case generation failed",
                        doc_id=parsed_doc.id,
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "edge_cases": []
            }
    
    async def generate_test_data_from_document(
        self,
        parsed_doc: ParsedDocument,
        test_scenarios: List[TestScenario]
    ) -> Dict[str, Any]:
        """Generate test data based on document content and scenarios"""
        
        logger.info("Generating test data from document",
                   doc_id=parsed_doc.id,
                   scenario_count=len(test_scenarios))
        
        try:
            # Extract data patterns from document
            data_patterns = self._extract_data_patterns(parsed_doc)
            
            # Build prompt for test data generation
            scenario_descriptions = [
                f"{scenario.name}: {scenario.description}"
                for scenario in test_scenarios
            ]
            
            llm_response = await self._call_llm_service({
                "provider": "openai",
                "model": "gpt-4",
                "prompt": self._build_test_data_prompt(data_patterns, scenario_descriptions),
                "context": {
                    "role": "Test Data Specialist",
                    "task": "Generate comprehensive test data sets",
                    "format": "JSON with test data for each scenario"
                },
                "max_tokens": 1500,
                "temperature": 0.5
            })
            
            if not llm_response.get("success"):
                return {
                    "success": False,
                    "error": f"LLM service error: {llm_response.get('error')}",
                    "test_data": []
                }
            
            test_data = self._parse_test_data_response(
                llm_response["content"],
                parsed_doc
            )
            
            logger.info("Test data generated successfully",
                       doc_id=parsed_doc.id,
                       test_data_sets=len(test_data))
            
            return {
                "success": True,
                "test_data": test_data,
                "source_document": {
                    "id": parsed_doc.id,
                    "data_patterns_found": len(data_patterns)
                }
            }
            
        except Exception as e:
            logger.error("Test data generation failed",
                        doc_id=parsed_doc.id,
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "test_data": []
            }
    
    async def _call_llm_service(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to LLM Integration Service"""
        try:
            response = await self.client.post(
                f"{self.llm_service_url}/generate",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.json().get("content", ""),
                    "tokens_used": response.json().get("tokens_used", 0),
                    "processing_time": response.json().get("processing_time", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def _extract_requirements(self, parsed_doc: ParsedDocument) -> str:
        """Extract requirements from parsed document"""
        requirements = []
        
        # Look for requirements in sections
        for section in parsed_doc.content.sections:
            title = section.get("title", "").lower()
            content = section.get("content", "")
            
            # Identify requirements sections
            if any(keyword in title for keyword in [
                "requirement", "user story", "acceptance criteria", 
                "specification", "functional", "feature"
            ]):
                requirements.append(f"## {section.get('title', 'Section')}\n{content}")
        
        # If no specific sections found, use full text with some filtering
        if not requirements:
            text = parsed_doc.content.text
            # Split by paragraphs and filter for requirement-like content
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if any(keyword in para.lower() for keyword in [
                    "as a", "i want", "so that", "given", "when", "then",
                    "should", "must", "shall", "requirement", "feature"
                ]):
                    requirements.append(para)
        
        return '\n\n'.join(requirements)
    
    def _extract_features(self, parsed_doc: ParsedDocument) -> List[str]:
        """Extract feature descriptions from document"""
        features = []
        
        for section in parsed_doc.content.sections:
            title = section.get("title", "").lower()
            content = section.get("content", "")
            
            if any(keyword in title for keyword in [
                "feature", "functionality", "component", "module", "system"
            ]):
                features.append(content)
        
        return features
    
    def _extract_data_patterns(self, parsed_doc: ParsedDocument) -> List[Dict[str, Any]]:
        """Extract data patterns from document tables and content"""
        patterns = []
        
        # Extract from tables
        for table in parsed_doc.content.tables:
            if table.get("data"):
                patterns.append({
                    "type": "table",
                    "source": table.get("sheet_name", "table"),
                    "data": table["data"][:5],  # First 5 rows as sample
                    "headers": table.get("headers", [])
                })
        
        # Extract from text patterns (emails, phones, etc.)
        import re
        text = parsed_doc.content.text
        
        # Email pattern
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            patterns.append({
                "type": "email",
                "samples": emails[:3]
            })
        
        # Phone pattern
        phones = re.findall(r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b', text)
        if phones:
            patterns.append({
                "type": "phone",
                "samples": phones[:3]
            })
        
        return patterns
    
    def _build_requirements_prompt(self, requirements_text: str, target_url: Optional[str] = None) -> str:
        """Build prompt for requirements to test conversion"""
        url_context = f"Target URL: {target_url}\n" if target_url else ""
        
        return f"""Convert the following requirements into comprehensive test scenarios:

{url_context}
Requirements:
{requirements_text}

Generate test scenarios that cover:
1. Happy path scenarios
2. Error handling and validation
3. Boundary conditions
4. User workflow testing
5. Data validation testing

Return a JSON array with this structure:
[
  {{
    "name": "Test scenario name",
    "description": "Detailed test description",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "expected_outcome": "What should happen",
    "priority": "high|medium|low",
    "test_type": "functional|integration|validation",
    "test_data": {{"key": "sample data needed"}}
  }}
]"""
    
    def _build_edge_case_prompt(self, features: List[str], existing_tests: List[str]) -> str:
        """Build prompt for edge case generation"""
        features_text = '\n'.join([f"- {feature}" for feature in features])
        existing_text = '\n'.join([f"- {test}" for test in existing_tests])
        
        return f"""Generate edge cases and negative test scenarios for the following features:

Features:
{features_text}

Existing tests to avoid duplicating:
{existing_text}

Focus on:
1. Boundary value testing
2. Invalid input handling
3. System limits and constraints
4. Network/connectivity issues
5. Permission and security edge cases
6. Data corruption scenarios
7. Race conditions and timing issues

Return JSON array with edge case test scenarios:
[
  {{
    "name": "Edge case name",
    "description": "What edge case this tests",
    "steps": ["Detailed steps"],
    "expected_outcome": "Expected behavior",
    "risk_level": "high|medium|low",
    "category": "boundary|security|performance|data"
  }}
]"""
    
    def _build_test_data_prompt(self, data_patterns: List[Dict[str, Any]], scenarios: List[str]) -> str:
        """Build prompt for test data generation"""
        patterns_text = json.dumps(data_patterns, indent=2)
        scenarios_text = '\n'.join([f"- {scenario}" for scenario in scenarios])
        
        return f"""Generate comprehensive test data for the following scenarios based on the data patterns found:

Data Patterns Found:
{patterns_text}

Test Scenarios:
{scenarios_text}

Generate test data including:
1. Valid data sets for positive testing
2. Invalid data for negative testing
3. Boundary values (min/max lengths, values)
4. Special characters and edge cases
5. Empty/null values
6. Realistic sample data

Return JSON with test data:
{{
  "test_data_sets": [
    {{
      "name": "Valid User Data",
      "description": "Complete valid data set",
      "data": {{"field": "value"}},
      "use_case": "positive testing"
    }}
  ]
}}"""
    
    def _parse_llm_test_response(self, llm_content: str, parsed_doc: ParsedDocument, target_url: Optional[str]) -> List[UITestCase]:
        """Parse LLM response into structured test cases"""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', llm_content, re.DOTALL)
            if json_match:
                scenarios_data = json.loads(json_match.group())
            else:
                # Fallback: assume entire response is JSON
                scenarios_data = json.loads(llm_content)
            
            if not isinstance(scenarios_data, list):
                scenarios_data = [scenarios_data]
            
            # Convert to TestScenario objects
            scenarios = []
            for scenario_data in scenarios_data:
                scenario = TestScenario(
                    name=scenario_data.get("name", "Generated Test"),
                    description=scenario_data.get("description", ""),
                    steps=scenario_data.get("steps", []),
                    expected_outcome=scenario_data.get("expected_outcome", ""),
                    priority=scenario_data.get("priority", "medium"),
                    test_type=scenario_data.get("test_type", "functional"),
                    metadata={
                        "test_data": scenario_data.get("test_data", {}),
                        "generated_from": parsed_doc.id
                    }
                )
                scenarios.append(scenario)
            
            # Create test case containing all scenarios
            test_case = UITestCase(
                name=f"Generated Tests - {parsed_doc.content.metadata.file_name if parsed_doc.content.metadata else 'Document'}",
                description=f"Test cases generated from {parsed_doc.source_type} document",
                scenarios=scenarios,
                target_url=target_url,
                metadata={
                    "source_document_id": parsed_doc.id,
                    "generation_method": "llm_requirements_conversion"
                }
            )
            
            return [test_case]
            
        except Exception as e:
            logger.error("Failed to parse LLM test response", error=str(e))
            return []
    
    def _parse_edge_case_response(self, llm_content: str, parsed_doc: ParsedDocument) -> List[TestScenario]:
        """Parse edge case response from LLM"""
        try:
            import re
            
            json_match = re.search(r'\[.*\]', llm_content, re.DOTALL)
            if json_match:
                edge_cases_data = json.loads(json_match.group())
            else:
                edge_cases_data = json.loads(llm_content)
            
            if not isinstance(edge_cases_data, list):
                edge_cases_data = [edge_cases_data]
            
            edge_cases = []
            for case_data in edge_cases_data:
                edge_case = TestScenario(
                    name=case_data.get("name", "Generated Edge Case"),
                    description=case_data.get("description", ""),
                    steps=case_data.get("steps", []),
                    expected_outcome=case_data.get("expected_outcome", ""),
                    priority="high",  # Edge cases are typically high priority
                    test_type="negative",
                    metadata={
                        "risk_level": case_data.get("risk_level", "medium"),
                        "category": case_data.get("category", "edge"),
                        "generated_from": parsed_doc.id
                    }
                )
                edge_cases.append(edge_case)
            
            return edge_cases
            
        except Exception as e:
            logger.error("Failed to parse edge case response", error=str(e))
            return []
    
    def _parse_test_data_response(self, llm_content: str, parsed_doc: ParsedDocument) -> List[Dict[str, Any]]:
        """Parse test data response from LLM"""
        try:
            import re
            
            json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            if json_match:
                test_data_response = json.loads(json_match.group())
            else:
                test_data_response = json.loads(llm_content)
            
            return test_data_response.get("test_data_sets", [])
            
        except Exception as e:
            logger.error("Failed to parse test data response", error=str(e))
            return []