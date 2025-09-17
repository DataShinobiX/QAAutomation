"""
Prompt Manager
Manages prompt templates for different AI tasks
"""
import os
import json
import structlog
from typing import Dict, Any, List
from jinja2 import Template, Environment, FileSystemLoader

logger = structlog.get_logger()


class PromptManager:
    """Manages AI prompt templates"""
    
    def __init__(self):
        self.prompts = {}
        self.prompt_sources = {}  # Store original template content
        self._load_default_prompts()
    
    def _load_default_prompts(self):
        """Load default prompt templates"""
        
        # Figma scenario generation prompt
        self.prompts["figma_scenario_generation"] = Template("""
You are a senior QA engineer analyzing a Figma design to generate comprehensive test scenarios.

Design Analysis:
- Design Name: {{ design_name }}
- Target URL: {{ target_url }}
- Key Frames: {{ frames }}

Task: Generate 3-5 realistic user journey test scenarios based on the Figma frames.

Requirements:
1. Focus on main user flows (login, navigation, forms, etc.)
2. Consider mobile and desktop interactions
3. Include both positive and negative test cases
4. Make scenarios actionable with specific steps

Output Format (JSON):
```json
[
  {
    "name": "User Login Flow",
    "description": "Test complete user authentication process",
    "steps": [
      "Navigate to login page",
      "Enter valid credentials",
      "Click login button",
      "Verify dashboard loads"
    ],
    "expected_result": "User successfully logs in and sees dashboard",
    "priority": "high"
  }
]
```

Generate realistic, actionable test scenarios:
""")

        # Minimal Figma scenario generation prompt (single component)
        self.prompts["figma_minimal_scenario_generation"] = Template("""
You are a QA engineer analyzing a single UI component from a Figma design.

Component Analysis:
- Frame: {{ frame_name }}
- Component Name: {{ component.name }}
- Component Type: {{ component.type }}
- Has Text: {{ component.has_text }}
- Interactive: {{ component.is_interactive }}

Design Context:
- Design: {{ design_context.design_name }}
- Target URL: {{ design_context.target_url }}
- Total Frames: {{ design_context.total_frames }}
- Total Components: {{ design_context.total_components }}

Task: Generate 2-3 focused test scenarios for this single component.

Requirements:
1. Keep scenarios simple and focused
2. Test the component's main functionality
3. Include one positive and one edge case scenario
4. Make tests actionable and specific

Output Format (JSON):
```json
[
  {
    "name": "Component Functionality Test",
    "description": "Test the main function of {{ component.name }}",
    "steps": [
      "Navigate to {{ design_context.target_url }}",
      "Locate the {{ component.name }} component",
      "Verify component is visible and accessible"
    ],
    "expected_result": "Component functions as expected",
    "priority": "high"
  }
]
```

Generate focused test scenarios for this component:
""")

        # UI test generation prompt
        self.prompts["ui_test_generation"] = Template("""
You are a QA automation engineer creating UI test cases from Figma components.

Frame Analysis:
- Frame Name: {{ frame_name }}
- Components: {{ components }}

Task: Generate specific UI test cases for the components.

Focus on:
1. Element existence and visibility
2. Text content verification
3. Interactive elements (buttons, inputs, links)
4. Layout and styling validation

Output Format (JSON):
```json
[
  {
    "component_name": "Login Button",
    "selector": "button[data-testid='login-btn']",
    "test_type": "clickable",
    "expected_value": null
  },
  {
    "component_name": "Email Input",
    "selector": "input[type='email']",
    "test_type": "exists",
    "expected_value": null
  }
]
```

Generate specific UI test cases:
""")

        # Minimal UI test generation prompt (single component)
        self.prompts["ui_test_minimal_generation"] = Template("""
You are a QA automation engineer creating UI tests for a single component.

Component Details:
- Name: {{ component.name }}
- Type: {{ component.type }}
- Has Text: {{ component.has_text }}
- Text Content: {{ component.text_content }}
- Interactive: {{ component.is_interactive }}
- Frame: {{ frame_name }}
- Target URL: {{ target_url }}

Task: Generate 1-2 specific UI test cases for this component only.

Focus on:
1. Element existence and visibility
2. Text content if applicable
3. Interaction capability if interactive

Output Format (JSON):
```json
[
  {
    "component_name": "{{ component.name }}",
    "selector": "button[data-testid='login-btn']",
    "test_type": "exists",
    "expected_value": null
  }
]
```

Generate focused UI test cases for this component:
""")

        # Edge case generation prompt
        self.prompts["edge_case_generation"] = Template("""
You are a QA specialist focused on edge case testing.

Feature: {{ feature_description }}

Existing Tests: {{ existing_tests }}

Task: Generate {{ test_count }} edge case scenarios that complement the existing tests.

Edge Case Categories to Consider:
1. Boundary conditions (min/max values, empty inputs)
2. Network issues (slow connections, timeouts)
3. Browser compatibility edge cases
4. User behavior extremes (rapid clicking, unusual input)
5. Data validation edge cases
6. Accessibility edge cases

Output Format (JSON):
```json
[
  {
    "name": "Empty Form Submission",
    "description": "Test behavior when user submits form with all empty fields",
    "steps": [
      "Navigate to form page",
      "Leave all fields empty",
      "Submit form",
      "Verify error messages appear"
    ],
    "expected_result": "Clear validation errors displayed for required fields"
  }
]
```

Generate creative but realistic edge cases:
""")

        # Test result analysis prompt
        self.prompts["test_result_analysis"] = Template("""
You are a senior QA analyst reviewing test execution results.

Test Results Summary:
{{ test_results }}

Failure Rate: {{ failure_rate }}%

Task: Provide comprehensive analysis and actionable recommendations.

Analysis Areas:
1. Overall test health assessment
2. Pattern identification in failures
3. Risk assessment for product quality
4. Prioritized recommendations for improvement
5. Potential root cause analysis

Output Format (JSON):
```json
{
  "summary": "Brief overall assessment",
  "insights": [
    "Key insight about test patterns",
    "Another important finding"
  ],
  "recommendations": [
    {
      "priority": "high",
      "action": "Specific action to take",
      "rationale": "Why this is important"
    }
  ],
  "risk_assessment": "low|medium|high",
  "quality_score": 85
}
```

Provide detailed analysis:
""")

        # Bug reproduction prompt
        self.prompts["bug_reproduction"] = Template("""
You are a bug reproduction specialist creating detailed steps to reproduce an issue.

Bug Report:
- Description: {{ bug_description }}
- Error Logs: {{ error_logs }}
- Screenshot Analysis: {{ screenshot_info }}

Task: Create comprehensive reproduction steps.

Requirements:
1. Clear, step-by-step instructions
2. Environment setup details
3. Expected vs actual behavior
4. Severity and category assessment

Output Format (JSON):
```json
{
  "title": "Clear bug title",
  "severity": "low|medium|high|critical",
  "category": "ui|functional|performance|security",
  "environment": {
    "browser": "Chrome 120+",
    "os": "Any",
    "screen_size": "Desktop (1920x1080)"
  },
  "steps": [
    "Step 1: Navigate to...",
    "Step 2: Click on...",
    "Step 3: Enter..."
  ],
  "expected_result": "What should happen",
  "actual_result": "What actually happens",
  "workaround": "Temporary solution if available"
}
```

Create detailed reproduction steps:
""")

        # Design edge cases prompt
        self.prompts["design_edge_cases"] = Template("""
You are analyzing a UI design to identify potential edge cases and unusual scenarios.

Design Summary: {{ design_summary }}
Frame Count: {{ frame_count }}

Task: Generate edge case scenarios specific to this design.

Consider:
1. Responsive behavior at different screen sizes
2. Content overflow scenarios (long text, many items)
3. Loading states and empty states
4. Interaction edge cases (hover, focus, disabled states)
5. Data validation scenarios
6. Accessibility considerations

Output Format (JSON):
```json
[
  {
    "name": "Long Username Display",
    "description": "Test behavior with extremely long usernames",
    "steps": [
      "Login with account having 50+ character username",
      "Navigate to profile page",
      "Verify text doesn't break layout"
    ],
    "expected_result": "Username is truncated or wraps gracefully"
  }
]
```

Generate design-specific edge cases:
""")

        # Requirement parsing prompt
        self.prompts["requirement_parsing"] = Template("""
You are a business analyst parsing requirements into structured format.

Requirements Text:
{{ requirements_text }}

Task: Extract and structure the requirements for test generation.

Parse into:
1. Individual user stories
2. Acceptance criteria
3. Business rules
4. Non-functional requirements

Output Format (JSON):
```json
[
  {
    "id": "REQ-001",
    "type": "user_story",
    "title": "User Login",
    "description": "As a user, I want to login so that I can access my account",
    "acceptance_criteria": [
      "User can enter email and password",
      "System validates credentials",
      "User is redirected to dashboard on success"
    ],
    "priority": "high",
    "category": "authentication"
  }
]
```

Parse and structure the requirements:
""")

        # Requirement scenarios prompt  
        self.prompts["requirement_scenarios"] = Template("""
You are creating test scenarios from a specific requirement.

Requirement: {{ requirement }}
Target URL: {{ target_url }}

Task: Generate 2-3 test scenarios for this requirement.

Include:
1. Happy path scenario
2. Error handling scenario  
3. Edge case scenario (if applicable)

Output Format (JSON):
```json
[
  {
    "name": "Successful User Registration",
    "description": "Test happy path user registration flow",
    "steps": [
      "Navigate to registration page",
      "Fill in all required fields with valid data",
      "Submit registration form",
      "Verify welcome email is sent"
    ],
    "expected_result": "User account created successfully"
  }
]
```

Generate comprehensive scenarios:
""")

        logger.info("Default prompts loaded", count=len(self.prompts))
    
    async def get_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Get rendered prompt with variables"""
        if template_name not in self.prompts:
            raise ValueError(f"Prompt template '{template_name}' not found")
        
        template = self.prompts[template_name]
        
        try:
            rendered = template.render(**variables)
            logger.debug("Rendered prompt template", 
                        template_name=template_name,
                        variables=list(variables.keys()))
            return rendered
        except Exception as e:
            logger.error("Failed to render prompt template",
                        template_name=template_name,
                        error=str(e))
            raise ValueError(f"Failed to render template: {str(e)}")
    
    async def get_available_prompts(self) -> List[Dict[str, Any]]:
        """Get list of available prompt templates"""
        prompts_info = []
        
        for name in self.prompts.keys():
            # Extract description from first few lines of template
            # Fallback description since Template.source is not available
            description = f"Template: {name}"
            
            prompts_info.append({
                "name": name,
                "description": description,
                "variables": self._extract_template_variables(name)
            })
        
        return prompts_info
    
    def _extract_template_variables(self, template_name: str) -> List[str]:
        """Extract variable names from template"""
        template = self.prompts[template_name]
        
        # Simple extraction of {{ variable }} patterns
        # Since Template.source is not available, use a fallback approach
        import re
        # For now, return common variables since we can't introspect the template
        common_variables = ["design_name", "target_url", "frames", "feature_description", "existing_tests", "test_count"]
        return common_variables
    
    def add_custom_prompt(self, name: str, template_content: str):
        """Add a custom prompt template"""
        try:
            template = Template(template_content)
            self.prompts[name] = template
            logger.info("Added custom prompt template", name=name)
        except Exception as e:
            logger.error("Failed to add custom prompt", name=name, error=str(e))
            raise ValueError(f"Invalid template: {str(e)}")
    
    async def execute_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        provider: str,
        model: str,
        llm_manager
    ) -> Dict[str, Any]:
        """Execute a prompt template with LLM"""
        try:
            # Get rendered prompt
            prompt = await self.get_prompt(template_name, variables)
            
            # Import here to avoid circular imports
            from models import LLMRequest, LLMProvider
            
            # Create LLM request
            request = LLMRequest(
                provider=LLMProvider(provider),
                model=model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.6
            )
            
            # Generate response
            response = await llm_manager.generate_text(request)
            
            return {
                "template_name": template_name,
                "variables": variables,
                "response": response.content,
                "tokens_used": response.tokens_used,
                "processing_time": response.processing_time
            }
            
        except Exception as e:
            logger.error("Failed to execute prompt",
                        template_name=template_name,
                        error=str(e))
            raise ValueError(f"Prompt execution failed: {str(e)}")
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate a template and return analysis"""
        try:
            template = Template(template_content)
            variables = self._extract_variables_from_content(template_content)
            
            return {
                "valid": True,
                "variables": variables,
                "variable_count": len(variables)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "variables": [],
                "variable_count": 0
            }
    
    def _extract_variables_from_content(self, content: str) -> List[str]:
        """Extract variables from template content"""
        import re
        variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', content)
        return list(set(variables))