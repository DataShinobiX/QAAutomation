"""
Smart Unified Test Generator
Intelligently combines Figma UI elements with documentation requirements
Handles gaps where UI elements aren't documented and vice versa
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import structlog
from datetime import datetime
import httpx
import json
import re

# Add shared modules to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

logger = structlog.get_logger()


class SmartUnifiedTestGenerator:
    """
    Smart Test Generator that:
    1. Extracts ALL UI elements from Figma (documented or not)
    2. Extracts ALL requirements from documentation
    3. Intelligently maps UI elements to requirements
    4. Generates tests for BOTH mapped and unmapped elements
    5. Creates comprehensive coverage with AI-powered gap analysis
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
    
    async def generate_smart_unified_tests(
        self,
        figma_file_key: str,
        requirements_document_path: str,
        target_url: str,
        project_name: str = "Smart Unified Test Project"
    ) -> Dict[str, Any]:
        """
        Generate smart unified test suite that handles all scenarios:
        1. UI elements WITH documentation coverage
        2. UI elements WITHOUT documentation coverage  
        3. Requirements WITHOUT UI implementation
        4. Edge cases and inferred functionality
        """
        
        logger.info("Starting smart unified test generation",
                   figma_file=figma_file_key,
                   requirements_doc=requirements_document_path,
                   target_url=target_url)
        
        try:
            # Step 1: Comprehensive Figma Analysis
            logger.info("Step 1: Comprehensive Figma UI analysis")
            figma_analysis = await self._comprehensive_figma_analysis(figma_file_key)
            
            if not figma_analysis["success"]:
                return {"success": False, "error": f"Figma analysis failed: {figma_analysis.get('error')}"}
            
            # Step 2: Comprehensive Requirements Analysis
            logger.info("Step 2: Comprehensive requirements analysis")
            requirements_analysis = await self._comprehensive_requirements_analysis(requirements_document_path)
            
            if not requirements_analysis["success"]:
                return {"success": False, "error": f"Requirements analysis failed: {requirements_analysis.get('error')}"}
            
            # Step 3: Smart Mapping Between UI and Requirements
            logger.info("Step 3: Smart mapping between UI elements and requirements")
            mapping_analysis = await self._smart_ui_requirement_mapping(
                figma_analysis["ui_data"],
                requirements_analysis["requirements_data"]
            )
            
            # Step 4: Generate Comprehensive Test Suite
            logger.info("Step 4: Generating comprehensive test suite")
            test_suite = await self._generate_comprehensive_test_suite(
                figma_analysis["ui_data"],
                requirements_analysis["requirements_data"],
                mapping_analysis,
                target_url,
                project_name
            )
            
            if not test_suite["success"]:
                return {"success": False, "error": f"Test suite generation failed: {test_suite.get('error')}"}
            
            # Step 5: Gap Analysis and Enhancement
            logger.info("Step 5: Gap analysis and test enhancement")
            enhanced_suite = await self._perform_gap_analysis_and_enhancement(
                test_suite["test_cases"],
                figma_analysis["ui_data"],
                requirements_analysis["requirements_data"],
                mapping_analysis
            )
            
            result = {
                "success": True,
                "project_name": project_name,
                "target_url": target_url,
                "generation_approach": "smart_unified_with_gap_analysis",
                "coverage_analysis": {
                    "total_figma_components": len(figma_analysis["ui_data"].get("all_components", [])),
                    "total_requirements": len(requirements_analysis["requirements_data"].get("all_requirements", [])),
                    "mapped_ui_elements": len(mapping_analysis.get("mapped_elements", [])),
                    "unmapped_ui_elements": len(mapping_analysis.get("unmapped_ui_elements", [])),
                    "unmapped_requirements": len(mapping_analysis.get("unmapped_requirements", [])),
                    "total_test_cases_generated": len(enhanced_suite)
                },
                "test_categories": {
                    "unified_documented_tests": [t for t in enhanced_suite if t.get("category") == "unified_documented"],
                    "ui_only_tests": [t for t in enhanced_suite if t.get("category") == "ui_only"],
                    "requirement_only_tests": [t for t in enhanced_suite if t.get("category") == "requirement_only"],
                    "inferred_functionality_tests": [t for t in enhanced_suite if t.get("category") == "inferred_functionality"],
                    "gap_analysis_tests": [t for t in enhanced_suite if t.get("category") == "gap_analysis"]
                },
                "all_test_cases": enhanced_suite,
                "source_data": {
                    "figma_analysis": figma_analysis["ui_data"],
                    "requirements_analysis": requirements_analysis["requirements_data"],
                    "mapping_analysis": mapping_analysis
                }
            }
            
            logger.info("Smart unified test generation completed successfully",
                       total_components=result["coverage_analysis"]["total_figma_components"],
                       total_requirements=result["coverage_analysis"]["total_requirements"],
                       mapped_elements=result["coverage_analysis"]["mapped_ui_elements"],
                       total_tests=result["coverage_analysis"]["total_test_cases_generated"])
            
            return result
            
        except Exception as e:
            logger.error("Smart unified test generation failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _comprehensive_figma_analysis(self, figma_file_key: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of ALL UI elements in Figma
        Extracts every component, button, form, text, image, etc.
        """
        try:
            response = await self.client.post(
                f"{self.figma_service_url}/analyze-figma-file",
                json={
                    "figma_file_key": figma_file_key,
                    "generate_tests": False,
                    "extract_components": True,
                    "analyze_interactions": True,
                    "deep_analysis": True  # Get ALL elements, not just main components
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Categorize ALL UI elements
                all_components = data.get("components", [])
                ui_categorization = self._categorize_ui_elements(all_components)
                
                return {
                    "success": True,
                    "ui_data": {
                        "all_components": all_components,
                        "interactive_elements": ui_categorization["interactive"],
                        "form_elements": ui_categorization["forms"],
                        "navigation_elements": ui_categorization["navigation"],
                        "content_elements": ui_categorization["content"],
                        "visual_elements": ui_categorization["visual"],
                        "uncategorized_elements": ui_categorization["uncategorized"],
                        "frames": data.get("frames", []),
                        "interactions": data.get("interactions", []),
                        "design_system": data.get("design_system", {})
                    }
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Figma analysis failed: {str(e)}"}
    
    def _categorize_ui_elements(self, components: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Intelligently categorize ALL UI elements from Figma"""
        
        categorization = {
            "interactive": [],
            "forms": [],
            "navigation": [],
            "content": [],
            "visual": [],
            "uncategorized": []
        }
        
        for component in components:
            component_name = component.get("name", "").lower()
            component_type = component.get("type", "").lower()
            
            # Interactive elements (buttons, links, clickable items)
            if any(keyword in component_name for keyword in [
                "button", "btn", "click", "submit", "action", "link", "tab", 
                "toggle", "switch", "checkbox", "radio", "select", "dropdown"
            ]) or component_type in ["button", "link"]:
                categorization["interactive"].append(component)
            
            # Form elements
            elif any(keyword in component_name for keyword in [
                "input", "field", "form", "text", "email", "password", "search",
                "textarea", "upload", "file", "date", "number", "phone"
            ]) or component_type in ["input", "form", "textfield"]:
                categorization["forms"].append(component)
            
            # Navigation elements
            elif any(keyword in component_name for keyword in [
                "nav", "menu", "header", "footer", "sidebar", "breadcrumb",
                "pagination", "step", "progress", "tab"
            ]) or component_type in ["navigation", "menu"]:
                categorization["navigation"].append(component)
            
            # Content elements
            elif any(keyword in component_name for keyword in [
                "text", "title", "heading", "label", "paragraph", "list",
                "card", "item", "content", "description", "message"
            ]) or component_type in ["text", "content"]:
                categorization["content"].append(component)
            
            # Visual elements
            elif any(keyword in component_name for keyword in [
                "image", "icon", "logo", "avatar", "photo", "graphic",
                "chart", "graph", "visual", "banner", "hero"
            ]) or component_type in ["image", "icon"]:
                categorization["visual"].append(component)
            
            # Uncategorized - these need smart inference
            else:
                categorization["uncategorized"].append(component)
        
        return categorization
    
    async def _comprehensive_requirements_analysis(self, document_path: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of ALL requirements in documentation
        Extracts user stories, business rules, technical requirements, etc.
        """
        try:
            # Parse document using document parser service
            with open(document_path, 'rb') as f:
                files = {'file': (os.path.basename(document_path), f, 'application/octet-stream')}
                
                response = await self.client.post(
                    f"{self.document_service_url}/parse/upload",
                    files=files
                )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Document parsing failed: {response.status_code}"}
            
            parse_result = response.json()
            if not parse_result.get("success"):
                return {"success": False, "error": f"Document parsing error: {parse_result.get('error')}"}
            
            parsed_doc = parse_result["document"]
            full_text = parsed_doc["content"]["text"]
            
            # Comprehensive requirement extraction
            requirements_data = {
                "document_id": parsed_doc["id"],
                "sections": parsed_doc["content"]["sections"],
                "full_text": full_text,
                "user_stories": self._extract_user_stories(full_text),
                "acceptance_criteria": self._extract_acceptance_criteria(full_text),
                "business_rules": self._extract_business_rules(full_text),
                "technical_requirements": self._extract_technical_requirements(full_text),
                "functional_requirements": self._extract_functional_requirements(full_text),
                "ui_requirements": self._extract_ui_requirements(full_text),
                "security_requirements": self._extract_security_requirements(full_text),
                "performance_requirements": self._extract_performance_requirements(full_text),
                "all_requirements": []  # Will be populated below
            }
            
            # Combine all requirements for mapping
            all_requirements = []
            all_requirements.extend(requirements_data["user_stories"])
            all_requirements.extend(requirements_data["functional_requirements"])
            all_requirements.extend(requirements_data["ui_requirements"])
            all_requirements.extend(requirements_data["business_rules"])
            requirements_data["all_requirements"] = all_requirements
            
            return {
                "success": True,
                "requirements_data": requirements_data
            }
            
        except Exception as e:
            return {"success": False, "error": f"Requirements analysis failed: {str(e)}"}
    
    def _extract_user_stories(self, text: str) -> List[Dict[str, Any]]:
        """Extract user stories with enhanced parsing"""
        user_stories = []
        
        # Enhanced patterns for user stories
        patterns = [
            r"As a[n]?\s+([^,]+),?\s+I want\s+([^,]+),?\s+so that\s+([^.\n]+)",
            r"User Story:?\s*(.+?)(?=\n\n|\n#|\nAcceptance|$)",
            r"Story:?\s*(.+?)(?=\n\n|\n#|\nAcceptance|$)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 3:
                    user_stories.append({
                        "type": "user_story",
                        "actor": match[0].strip(),
                        "action": match[1].strip(),
                        "benefit": match[2].strip(),
                        "full_text": f"As a {match[0].strip()}, I want {match[1].strip()}, so that {match[2].strip()}",
                        "priority": "medium",
                        "ui_related": self._is_ui_related(f"{match[1]} {match[2]}")
                    })
                elif isinstance(match, str):
                    user_stories.append({
                        "type": "user_story", 
                        "full_text": match.strip(),
                        "ui_related": self._is_ui_related(match)
                    })
        
        return user_stories[:20]  # Limit for performance
    
    def _extract_functional_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract functional requirements"""
        requirements = []
        
        patterns = [
            r"The system shall\s+([^.\n]+)",
            r"The application must\s+([^.\n]+)",
            r"System should\s+([^.\n]+)",
            r"Functionality:?\s*(.+?)(?=\n\n|\n#|$)",
            r"Feature:?\s*(.+?)(?=\n\n|\n#|$)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if match.strip():
                    requirements.append({
                        "type": "functional_requirement",
                        "text": match.strip(),
                        "ui_related": self._is_ui_related(match),
                        "priority": "high" if any(keyword in match.lower() for keyword in ["must", "shall", "required"]) else "medium"
                    })
        
        return requirements[:30]
    
    def _extract_ui_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract UI-specific requirements"""
        ui_requirements = []
        
        ui_keywords = [
            "button", "form", "field", "input", "page", "screen", "interface",
            "menu", "navigation", "layout", "design", "display", "show", "hide",
            "click", "select", "dropdown", "checkbox", "radio", "upload",
            "modal", "popup", "dialog", "tooltip", "tab", "accordion"
        ]
        
        # Look for sentences containing UI keywords
        sentences = re.split(r'[.!?]\s*', text)
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ui_keywords):
                ui_requirements.append({
                    "type": "ui_requirement",
                    "text": sentence.strip(),
                    "ui_related": True,
                    "priority": "high",
                    "ui_elements": [keyword for keyword in ui_keywords if keyword in sentence.lower()]
                })
        
        return ui_requirements[:25]
    
    def _extract_technical_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract technical requirements"""
        tech_requirements = []
        
        tech_patterns = [
            r"Technical Requirement:?\s*(.+?)(?=\n\n|\n#|$)",
            r"Performance:?\s*(.+?)(?=\n\n|\n#|$)",
            r"Security:?\s*(.+?)(?=\n\n|\n#|$)",
            r"The system must support\s+([^.\n]+)",
            r"Response time must be\s+([^.\n]+)"
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if match.strip():
                    tech_requirements.append({
                        "type": "technical_requirement",
                        "text": match.strip(),
                        "testable": True,
                        "priority": "medium"
                    })
        
        return tech_requirements[:15]
    
    def _extract_security_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract security requirements"""
        security_requirements = []
        
        security_keywords = [
            "authentication", "authorization", "login", "password", "security",
            "encrypt", "https", "token", "session", "access control", "permission"
        ]
        
        sentences = re.split(r'[.!?]\s*', text)
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in security_keywords):
                security_requirements.append({
                    "type": "security_requirement",
                    "text": sentence.strip(),
                    "priority": "high",
                    "ui_related": self._is_ui_related(sentence)
                })
        
        return security_requirements[:10]
    
    def _extract_performance_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract performance requirements"""
        perf_requirements = []
        
        perf_patterns = [
            r"load time.*?(\d+)\s*(second|ms|millisecond)",
            r"response time.*?(\d+)\s*(second|ms|millisecond)",
            r"concurrent users.*?(\d+)",
            r"performance.*?(\d+.*?(?:second|ms|user))"
        ]
        
        for pattern in perf_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                perf_requirements.append({
                    "type": "performance_requirement",
                    "text": f"Performance requirement: {match}",
                    "testable": True,
                    "priority": "medium"
                })
        
        return perf_requirements[:10]
    
    def _extract_business_rules(self, text: str) -> List[Dict[str, Any]]:
        """Extract business rules"""
        business_rules = []
        
        rule_patterns = [
            r"Business Rule:?\s*(.+?)(?=\n\n|\n#|$)",
            r"Rule:?\s*(.+?)(?=\n\n|\n#|$)",
            r"Users cannot\s+([^.\n]+)",
            r"System must not\s+([^.\n]+)",
            r"Only.*?can\s+([^.\n]+)"
        ]
        
        for pattern in rule_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if match.strip():
                    business_rules.append({
                        "type": "business_rule",
                        "text": match.strip(),
                        "ui_related": self._is_ui_related(match),
                        "priority": "high"
                    })
        
        return business_rules[:15]
    
    def _extract_acceptance_criteria(self, text: str) -> List[Dict[str, Any]]:
        """Extract acceptance criteria"""
        criteria = []
        
        criteria_patterns = [
            r"Acceptance Criteria:?\s*\n?(.+?)(?=\n\n|\n#|\nUser Story|$)",
            r"Given\s+([^,]+),?\s+when\s+([^,]+),?\s+then\s+([^.\n]+)",
            r"Verify that\s+([^.\n]+)",
            r"Ensure that\s+([^.\n]+)"
        ]
        
        for pattern in criteria_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    criteria.append({
                        "type": "acceptance_criteria",
                        "given": match[0].strip() if len(match) > 0 else "",
                        "when": match[1].strip() if len(match) > 1 else "",
                        "then": match[2].strip() if len(match) > 2 else "",
                        "ui_related": self._is_ui_related(' '.join(match))
                    })
                elif isinstance(match, str):
                    criteria.append({
                        "type": "acceptance_criteria",
                        "text": match.strip(),
                        "ui_related": self._is_ui_related(match)
                    })
        
        return criteria[:20]
    
    def _is_ui_related(self, text: str) -> bool:
        """Determine if requirement text is UI-related"""
        ui_indicators = [
            "button", "form", "field", "input", "page", "screen", "click",
            "select", "display", "show", "hide", "navigation", "menu", "link",
            "interface", "layout", "design", "view", "modal", "popup", "tab"
        ]
        
        return any(indicator in text.lower() for indicator in ui_indicators)
    
    async def _smart_ui_requirement_mapping(
        self, 
        ui_data: Dict[str, Any], 
        requirements_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Smart mapping between UI elements and requirements using AI
        Identifies which UI elements have documentation coverage and which don't
        """
        try:
            # Prepare data for AI analysis
            ui_elements = ui_data.get("all_components", [])
            all_requirements = requirements_data.get("all_requirements", [])
            
            # Use AI to perform intelligent mapping
            mapping_prompt = self._build_mapping_prompt(ui_elements, all_requirements)
            
            response = await self.client.post(
                f"{self.llm_service_url}/llm/generate",
                json={
                    "provider": "openai",
                    "model": "gpt-4",
                    "prompt": mapping_prompt,
                    "context": {
                        "role": "Senior QA Analyst specialized in requirement traceability",
                        "task": "Map UI elements to requirements and identify gaps",
                        "format": "JSON mapping with gap analysis"
                    },
                    "max_tokens": 2500,
                    "temperature": 0.2  # Low temperature for consistent mapping
                }
            )
            
            if response.status_code != 200:
                # Fallback to rule-based mapping
                return self._fallback_mapping(ui_elements, all_requirements)
            
            ai_result = response.json()
            if not ai_result.get("success"):
                return self._fallback_mapping(ui_elements, all_requirements)
            
            # Parse AI mapping response
            ai_content = ai_result.get("response", {}).get("content", "")
            mapping_data = self._parse_mapping_response(ai_content)
            
            # Enhance with additional analysis
            enhanced_mapping = self._enhance_mapping_analysis(
                mapping_data, ui_elements, all_requirements
            )
            
            return enhanced_mapping
            
        except Exception as e:
            logger.error("Smart mapping failed, using fallback", error=str(e))
            return self._fallback_mapping(ui_elements, all_requirements)
    
    def _build_mapping_prompt(self, ui_elements: List[Dict], requirements: List[Dict]) -> str:
        """Build prompt for AI-powered UI-requirement mapping"""
        
        # Summarize UI elements
        ui_summary = []
        for element in ui_elements[:20]:  # Limit for prompt size
            ui_summary.append(f"- {element.get('name', 'Unknown')}: {element.get('type', 'component')}")
        
        # Summarize requirements
        req_summary = []
        for req in requirements[:15]:  # Limit for prompt size
            if isinstance(req, dict):
                text = req.get('full_text', req.get('text', str(req)))
                req_summary.append(f"- {text[:100]}...")
        
        prompt = f"""# UI Element to Requirement Mapping Analysis

## UI Elements Identified:
{chr(10).join(ui_summary)}

## Requirements Identified:
{chr(10).join(req_summary)}

## Task: Smart Mapping and Gap Analysis

Analyze the UI elements and requirements to create intelligent mappings. For each UI element, determine:
1. Is it mentioned/covered in requirements?
2. What requirement(s) does it fulfill?
3. What functionality can be inferred if not documented?

For requirements, determine:
1. Which UI elements support this requirement?
2. Are there missing UI elements needed for this requirement?

Return JSON format:
```json
{{
  "mapped_elements": [
    {{
      "ui_element": "LoginButton",
      "requirements": ["User authentication story", "Login functionality requirement"],
      "confidence": "high",
      "mapping_type": "explicit"
    }}
  ],
  "unmapped_ui_elements": [
    {{
      "ui_element": "ForgotPasswordLink", 
      "inferred_functionality": "Password reset workflow",
      "test_priority": "medium",
      "reason": "UI element exists but not documented in requirements"
    }}
  ],
  "unmapped_requirements": [
    {{
      "requirement": "Two-factor authentication",
      "missing_ui": ["2FA input field", "verification code entry"],
      "implementation_gap": true
    }}
  ],
  "coverage_analysis": {{
    "ui_coverage_percentage": 75,
    "requirement_coverage_percentage": 85,
    "gaps_identified": 3
  }}
}}
```"""
        
        return prompt
    
    def _parse_mapping_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI mapping response into structured data"""
        try:
            import re
            
            # Extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                mapping_data = json.loads(json_match.group())
                return mapping_data
            else:
                # Fallback parsing
                return {
                    "mapped_elements": [],
                    "unmapped_ui_elements": [],
                    "unmapped_requirements": [],
                    "coverage_analysis": {"ui_coverage_percentage": 50, "requirement_coverage_percentage": 50, "gaps_identified": 0}
                }
                
        except Exception as e:
            logger.error("Failed to parse mapping response", error=str(e))
            return {
                "mapped_elements": [],
                "unmapped_ui_elements": [], 
                "unmapped_requirements": [],
                "coverage_analysis": {"ui_coverage_percentage": 0, "requirement_coverage_percentage": 0, "gaps_identified": 0}
            }
    
    def _fallback_mapping(self, ui_elements: List[Dict], requirements: List[Dict]) -> Dict[str, Any]:
        """Fallback rule-based mapping when AI fails"""
        mapped_elements = []
        unmapped_ui = []
        unmapped_req = []
        
        # Simple keyword-based mapping
        for ui_element in ui_elements:
            ui_name = ui_element.get("name", "").lower()
            found_match = False
            
            for req in requirements:
                req_text = ""
                if isinstance(req, dict):
                    req_text = req.get('full_text', req.get('text', '')).lower()
                else:
                    req_text = str(req).lower()
                
                # Simple keyword matching
                if any(keyword in req_text for keyword in ui_name.split() if len(keyword) > 2):
                    mapped_elements.append({
                        "ui_element": ui_element.get("name"),
                        "requirements": [req_text[:100]],
                        "confidence": "low",
                        "mapping_type": "keyword_based"
                    })
                    found_match = True
                    break
            
            if not found_match:
                unmapped_ui.append({
                    "ui_element": ui_element.get("name"),
                    "inferred_functionality": f"Inferred functionality for {ui_element.get('name')}",
                    "test_priority": "medium"
                })
        
        return {
            "mapped_elements": mapped_elements,
            "unmapped_ui_elements": unmapped_ui,
            "unmapped_requirements": unmapped_req,
            "coverage_analysis": {
                "ui_coverage_percentage": 60,
                "requirement_coverage_percentage": 70,
                "gaps_identified": len(unmapped_ui) + len(unmapped_req)
            }
        }
    
    def _enhance_mapping_analysis(
        self, 
        mapping_data: Dict[str, Any], 
        ui_elements: List[Dict], 
        requirements: List[Dict]
    ) -> Dict[str, Any]:
        """Enhance mapping with additional analysis"""
        
        # Add priority scoring
        for element in mapping_data.get("mapped_elements", []):
            element["test_priority"] = self._calculate_test_priority(element)
        
        for element in mapping_data.get("unmapped_ui_elements", []):
            element["test_priority"] = self._calculate_unmapped_ui_priority(element)
        
        # Add test generation hints
        mapping_data["test_generation_strategy"] = {
            "high_priority_mapped": len([e for e in mapping_data.get("mapped_elements", []) if e.get("test_priority") == "high"]),
            "medium_priority_mapped": len([e for e in mapping_data.get("mapped_elements", []) if e.get("test_priority") == "medium"]),
            "unmapped_ui_count": len(mapping_data.get("unmapped_ui_elements", [])),
            "gap_count": len(mapping_data.get("unmapped_requirements", [])),
            "recommended_approach": "comprehensive_with_gap_filling"
        }
        
        return mapping_data
    
    def _calculate_test_priority(self, mapped_element: Dict[str, Any]) -> str:
        """Calculate test priority for mapped elements"""
        confidence = mapped_element.get("confidence", "low")
        ui_element = mapped_element.get("ui_element", "").lower()
        
        # High priority for critical UI elements
        critical_elements = ["login", "submit", "save", "delete", "payment", "checkout", "register"]
        
        if any(critical in ui_element for critical in critical_elements):
            return "high"
        elif confidence == "high":
            return "high"
        elif confidence == "medium":
            return "medium"
        else:
            return "low"
    
    def _calculate_unmapped_ui_priority(self, unmapped_element: Dict[str, Any]) -> str:
        """Calculate test priority for unmapped UI elements"""
        ui_element = unmapped_element.get("ui_element", "").lower()
        
        # High priority for elements that should definitely be tested
        critical_patterns = ["error", "warning", "delete", "submit", "save", "cancel", "confirm"]
        medium_patterns = ["filter", "sort", "search", "navigation", "menu"]
        
        if any(pattern in ui_element for pattern in critical_patterns):
            return "high"
        elif any(pattern in ui_element for pattern in medium_patterns):
            return "medium"
        else:
            return "low"
    
    async def _generate_comprehensive_test_suite(
        self,
        ui_data: Dict[str, Any],
        requirements_data: Dict[str, Any],
        mapping_analysis: Dict[str, Any],
        target_url: str,
        project_name: str
    ) -> Dict[str, Any]:
        """Generate comprehensive test suite covering all scenarios"""
        
        try:
            test_categories = {
                "unified_documented_tests": [],
                "ui_only_tests": [],
                "requirement_only_tests": [],
                "inferred_functionality_tests": [],
                "gap_analysis_tests": []
            }
            
            # 1. Generate tests for mapped elements (UI + Requirements)
            unified_tests = await self._generate_unified_documented_tests(
                mapping_analysis.get("mapped_elements", []),
                target_url
            )
            test_categories["unified_documented_tests"] = unified_tests
            
            # 2. Generate tests for unmapped UI elements
            ui_only_tests = await self._generate_ui_only_tests(
                mapping_analysis.get("unmapped_ui_elements", []),
                target_url
            )
            test_categories["ui_only_tests"] = ui_only_tests
            
            # 3. Generate tests for unmapped requirements
            req_only_tests = await self._generate_requirement_only_tests(
                mapping_analysis.get("unmapped_requirements", []),
                target_url
            )
            test_categories["requirement_only_tests"] = req_only_tests
            
            # 4. Generate inferred functionality tests
            inferred_tests = await self._generate_inferred_functionality_tests(
                ui_data, requirements_data, mapping_analysis, target_url
            )
            test_categories["inferred_functionality_tests"] = inferred_tests
            
            # 5. Generate gap analysis tests
            gap_tests = await self._generate_gap_analysis_tests(
                mapping_analysis, target_url
            )
            test_categories["gap_analysis_tests"] = gap_tests
            
            # Combine all test cases
            all_tests = []
            for category, tests in test_categories.items():
                for test in tests:
                    test["category"] = category
                    all_tests.append(test)
            
            return {
                "success": True,
                "test_cases": all_tests,
                "test_categories": test_categories,
                "generation_summary": {
                    "total_tests": len(all_tests),
                    "unified_tests": len(unified_tests),
                    "ui_only_tests": len(ui_only_tests),
                    "requirement_only_tests": len(req_only_tests),
                    "inferred_tests": len(inferred_tests),
                    "gap_tests": len(gap_tests)
                }
            }
            
        except Exception as e:
            logger.error("Test suite generation failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _generate_unified_documented_tests(
        self, mapped_elements: List[Dict[str, Any]], target_url: str
    ) -> List[Dict[str, Any]]:
        """Generate tests for UI elements that have documentation coverage"""
        
        unified_tests = []
        
        for mapped_element in mapped_elements:
            ui_element = mapped_element.get("ui_element", "")
            requirements = mapped_element.get("requirements", [])
            confidence = mapped_element.get("confidence", "medium")
            
            # Create comprehensive test that validates both UI and requirements
            test_case = {
                "id": f"unified_{hash(ui_element)}",
                "name": f"Unified Test: {ui_element} with Requirements Validation",
                "description": f"Comprehensive test that validates {ui_element} UI functionality and fulfills requirements: {', '.join(requirements[:2])}",
                "test_type": "unified_documented",
                "priority": "high" if confidence == "high" else "medium",
                "ui_element": ui_element,
                "requirements_covered": requirements,
                "steps": [
                    f"Navigate to {target_url}",
                    f"Locate UI element '{ui_element}' and verify it matches Figma design",
                    f"Verify element is accessible and follows design specifications",
                    f"Test element functionality as per requirements: {requirements[0] if requirements else 'basic functionality'}",
                    f"Validate business logic and expected outcomes",
                    f"Verify error handling and edge cases",
                    f"Confirm integration with related UI components"
                ],
                "expected_results": [
                    f"UI element '{ui_element}' is present and matches design",
                    "Element functionality works as documented in requirements",
                    "Business logic is properly implemented",
                    "Error handling works correctly",
                    "Integration with other components is seamless"
                ],
                "validation_points": [
                    f"Visual: {ui_element} matches Figma specifications",
                    f"Functional: Requirements {requirements[:1]} are fulfilled",
                    "Integration: Element works within overall user workflow"
                ],
                "mapping_confidence": confidence
            }
            
            unified_tests.append(test_case)
        
        return unified_tests
    
    async def _generate_ui_only_tests(
        self, unmapped_ui_elements: List[Dict[str, Any]], target_url: str
    ) -> List[Dict[str, Any]]:
        """Generate tests for UI elements without documentation coverage"""
        
        ui_only_tests = []
        
        for ui_element in unmapped_ui_elements:
            element_name = ui_element.get("ui_element", "")
            inferred_functionality = ui_element.get("inferred_functionality", "")
            priority = ui_element.get("test_priority", "medium")
            
            test_case = {
                "id": f"ui_only_{hash(element_name)}",
                "name": f"UI Element Test: {element_name} (Undocumented)",
                "description": f"Test undocumented UI element '{element_name}' with inferred functionality: {inferred_functionality}",
                "test_type": "ui_only_undocumented",
                "priority": priority,
                "ui_element": element_name,
                "inferred_functionality": inferred_functionality,
                "documentation_gap": True,
                "steps": [
                    f"Navigate to {target_url}",
                    f"Locate UI element '{element_name}'",
                    f"Verify element is visible and properly styled",
                    f"Test basic interaction (click, hover, focus as appropriate)",
                    f"Verify expected behavior based on element type and name",
                    f"Test edge cases and error conditions",
                    f"Document actual behavior for requirement gap analysis"
                ],
                "expected_results": [
                    f"UI element '{element_name}' is present and functional",
                    "Element behaves consistently with similar UI patterns",
                    "No critical errors or broken functionality",
                    "Element follows accessibility best practices"
                ],
                "validation_points": [
                    f"Visual: {element_name} is properly rendered",
                    f"Functional: Inferred functionality '{inferred_functionality}' works",
                    "Gap: Document behavior for requirements update"
                ],
                "recommendations": [
                    f"Add documentation for {element_name} functionality",
                    "Verify if this element should have formal requirements",
                    "Consider if additional validation is needed"
                ]
            }
            
            ui_only_tests.append(test_case)
        
        return ui_only_tests
    
    async def _generate_requirement_only_tests(
        self, unmapped_requirements: List[Dict[str, Any]], target_url: str
    ) -> List[Dict[str, Any]]:
        """Generate tests for requirements without UI implementation"""
        
        req_only_tests = []
        
        for requirement in unmapped_requirements:
            req_text = requirement.get("requirement", "")
            missing_ui = requirement.get("missing_ui", [])
            
            test_case = {
                "id": f"req_only_{hash(req_text)}",
                "name": f"Requirement Test: {req_text[:50]}... (Missing UI)",
                "description": f"Test for documented requirement without UI implementation: {req_text}",
                "test_type": "requirement_only_missing_ui",
                "priority": "high",  # High priority because it's a gap
                "requirement": req_text,
                "missing_ui_elements": missing_ui,
                "implementation_gap": True,
                "steps": [
                    f"Navigate to {target_url}",
                    f"Look for UI elements that should support requirement: {req_text[:100]}",
                    f"Verify if missing UI elements exist: {', '.join(missing_ui)}",
                    f"Test alternative ways this requirement might be implemented",
                    f"Document gaps between requirements and actual implementation"
                ],
                "expected_results": [
                    "Requirement should be supported by appropriate UI elements",
                    f"Missing UI elements should be identified: {', '.join(missing_ui)}",
                    "Alternative implementation paths should be evaluated"
                ],
                "validation_points": [
                    f"Gap: Requirement '{req_text[:50]}...' has no UI support",
                    f"Missing: UI elements {missing_ui} are not implemented",
                    "Impact: Functionality gap affects user experience"
                ],
                "recommendations": [
                    f"Implement missing UI elements: {', '.join(missing_ui)}",
                    "Review requirement for implementation feasibility",
                    "Update design to include necessary UI components"
                ]
            }
            
            req_only_tests.append(test_case)
        
        return req_only_tests
    
    async def _generate_inferred_functionality_tests(
        self,
        ui_data: Dict[str, Any],
        requirements_data: Dict[str, Any], 
        mapping_analysis: Dict[str, Any],
        target_url: str
    ) -> List[Dict[str, Any]]:
        """Generate tests for inferred functionality based on UI patterns"""
        
        inferred_tests = []
        
        # Look for common UI patterns that suggest standard functionality
        ui_elements = ui_data.get("all_components", [])
        
        for element in ui_elements:
            element_name = element.get("name", "").lower()
            
            # Infer functionality based on naming patterns
            inferred_functionality = None
            test_priority = "low"
            
            if "search" in element_name:
                inferred_functionality = "Search functionality with results filtering"
                test_priority = "high"
            elif "filter" in element_name:
                inferred_functionality = "Content filtering and sorting"
                test_priority = "medium"
            elif "pagination" in element_name or "page" in element_name:
                inferred_functionality = "Content pagination navigation"
                test_priority = "medium"
            elif "sort" in element_name:
                inferred_functionality = "Content sorting by various criteria"
                test_priority = "medium"
            elif "export" in element_name or "download" in element_name:
                inferred_functionality = "Data export and download functionality"
                test_priority = "high"
            elif "refresh" in element_name or "reload" in element_name:
                inferred_functionality = "Data refresh and reload capability"
                test_priority = "low"
            
            if inferred_functionality:
                test_case = {
                    "id": f"inferred_{hash(element_name)}",
                    "name": f"Inferred Functionality Test: {element.get('name')}",
                    "description": f"Test inferred functionality for {element.get('name')}: {inferred_functionality}",
                    "test_type": "inferred_functionality",
                    "priority": test_priority,
                    "ui_element": element.get("name"),
                    "inferred_functionality": inferred_functionality,
                    "steps": [
                        f"Navigate to {target_url}",
                        f"Locate {element.get('name')} element",
                        f"Test inferred functionality: {inferred_functionality}",
                        f"Verify behavior matches common UI patterns",
                        f"Test edge cases for inferred functionality",
                        f"Validate integration with related elements"
                    ],
                    "expected_results": [
                        f"Element {element.get('name')} provides expected functionality",
                        "Behavior is consistent with UI pattern standards",
                        "Functionality integrates well with overall system"
                    ],
                    "validation_points": [
                        f"Pattern: {element.get('name')} follows standard UI conventions",
                        f"Function: {inferred_functionality} works as expected",
                        "UX: Functionality enhances user experience"
                    ]
                }
                
                inferred_tests.append(test_case)
        
        return inferred_tests
    
    async def _generate_gap_analysis_tests(
        self, mapping_analysis: Dict[str, Any], target_url: str
    ) -> List[Dict[str, Any]]:
        """Generate tests specifically for identified gaps and inconsistencies"""
        
        gap_tests = []
        
        coverage_analysis = mapping_analysis.get("coverage_analysis", {})
        ui_coverage = coverage_analysis.get("ui_coverage_percentage", 0)
        req_coverage = coverage_analysis.get("requirement_coverage_percentage", 0)
        
        # Generate overall coverage validation test
        if ui_coverage < 80 or req_coverage < 80:
            coverage_test = {
                "id": "gap_coverage_analysis",
                "name": "Coverage Gap Analysis Test",
                "description": f"Comprehensive test to validate UI coverage ({ui_coverage}%) and requirement coverage ({req_coverage}%)",
                "test_type": "gap_analysis_coverage",
                "priority": "high",
                "coverage_metrics": {
                    "ui_coverage": ui_coverage,
                    "requirement_coverage": req_coverage
                },
                "steps": [
                    f"Navigate to {target_url}",
                    "Systematically test all visible UI elements",
                    "Compare against Figma design specifications",
                    "Validate against documented requirements",
                    "Identify any functionality gaps or inconsistencies",
                    "Document uncovered elements and missing requirements"
                ],
                "expected_results": [
                    "All UI elements have corresponding documentation or justification",
                    "All requirements have UI implementation or alternative solution",
                    "Coverage gaps are identified and prioritized for resolution"
                ],
                "validation_points": [
                    f"Coverage: UI coverage should increase from {ui_coverage}%",
                    f"Coverage: Requirement coverage should increase from {req_coverage}%",
                    "Gap: All gaps are documented with remediation plan"
                ]
            }
            
            gap_tests.append(coverage_test)
        
        # Generate specific gap tests for high-impact missing elements
        unmapped_ui = mapping_analysis.get("unmapped_ui_elements", [])
        high_impact_ui = [ui for ui in unmapped_ui if ui.get("test_priority") == "high"]
        
        if high_impact_ui:
            high_impact_test = {
                "id": "gap_high_impact_ui",
                "name": "High Impact Undocumented UI Elements Test",
                "description": "Focused testing of high-impact UI elements that lack documentation",
                "test_type": "gap_analysis_high_impact",
                "priority": "high",
                "high_impact_elements": [ui.get("ui_element") for ui in high_impact_ui],
                "steps": [
                    f"Navigate to {target_url}",
                    f"Focus on high-impact elements: {', '.join([ui.get('ui_element') for ui in high_impact_ui[:3]])}",
                    "Test critical functionality for each element",
                    "Verify these elements are essential for user workflows",
                    "Document business impact of these undocumented elements",
                    "Recommend priority for adding formal documentation"
                ],
                "expected_results": [
                    "High-impact elements function correctly",
                    "Business importance is clearly established",
                    "Documentation gaps are prioritized for resolution"
                ]
            }
            
            gap_tests.append(high_impact_test)
        
        return gap_tests
    
    async def _perform_gap_analysis_and_enhancement(
        self,
        test_cases: List[Dict[str, Any]],
        ui_data: Dict[str, Any],
        requirements_data: Dict[str, Any], 
        mapping_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Final gap analysis and test suite enhancement"""
        
        enhanced_tests = []
        
        for test_case in test_cases:
            # Add gap analysis metadata to each test
            enhanced_test = {
                **test_case,
                "gap_analysis": {
                    "coverage_contribution": self._calculate_coverage_contribution(test_case),
                    "risk_mitigation": self._calculate_risk_mitigation(test_case),
                    "business_impact": self._calculate_business_impact(test_case)
                },
                "enhancement_suggestions": self._generate_enhancement_suggestions(test_case)
            }
            
            enhanced_tests.append(enhanced_test)
        
        # Sort tests by priority and impact
        enhanced_tests.sort(key=lambda t: (
            {"high": 3, "medium": 2, "low": 1}.get(t.get("priority", "low"), 1),
            t.get("gap_analysis", {}).get("business_impact", 0)
        ), reverse=True)
        
        return enhanced_tests
    
    def _calculate_coverage_contribution(self, test_case: Dict[str, Any]) -> str:
        """Calculate how much this test contributes to overall coverage"""
        test_type = test_case.get("test_type", "")
        
        if "unified" in test_type:
            return "high"  # Tests both UI and requirements
        elif "gap_analysis" in test_type:
            return "high"  # Fills important gaps
        elif "ui_only" in test_type or "requirement_only" in test_type:
            return "medium"  # Covers one dimension
        else:
            return "low"
    
    def _calculate_risk_mitigation(self, test_case: Dict[str, Any]) -> str:
        """Calculate risk mitigation value of this test"""
        priority = test_case.get("priority", "low")
        has_gaps = test_case.get("implementation_gap", False) or test_case.get("documentation_gap", False)
        
        if priority == "high" and has_gaps:
            return "critical"
        elif priority == "high":
            return "high"
        elif has_gaps:
            return "medium"
        else:
            return "low"
    
    def _calculate_business_impact(self, test_case: Dict[str, Any]) -> int:
        """Calculate business impact score (0-10)"""
        score = 5  # Base score
        
        # Increase for unified tests
        if "unified" in test_case.get("test_type", ""):
            score += 2
        
        # Increase for high priority
        if test_case.get("priority") == "high":
            score += 2
        
        # Increase for gap-filling tests
        if test_case.get("implementation_gap") or test_case.get("documentation_gap"):
            score += 1
        
        # Increase for critical UI elements
        ui_element = test_case.get("ui_element", "").lower()
        critical_elements = ["login", "payment", "checkout", "submit", "save", "delete"]
        if any(critical in ui_element for critical in critical_elements):
            score += 2
        
        return min(score, 10)  # Cap at 10
    
    def _generate_enhancement_suggestions(self, test_case: Dict[str, Any]) -> List[str]:
        """Generate suggestions for enhancing this test"""
        suggestions = []
        
        if test_case.get("documentation_gap"):
            suggestions.append("Consider adding formal documentation for this UI element")
        
        if test_case.get("implementation_gap"):
            suggestions.append("Implement missing UI elements to fulfill requirements")
        
        if test_case.get("priority") == "high":
            suggestions.append("Prioritize this test in execution order")
        
        if "inferred" in test_case.get("test_type", ""):
            suggestions.append("Validate inferred functionality with product team")
        
        if test_case.get("gap_analysis", {}).get("business_impact", 0) > 7:
            suggestions.append("High business impact - consider automated testing")
        
        return suggestions