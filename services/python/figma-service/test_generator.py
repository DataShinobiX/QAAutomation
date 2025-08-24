"""
UI Test Generator
Generates UI test cases from Figma design analysis
"""
import asyncio
import structlog
from typing import Dict, List, Optional, Any
import re

from config import FigmaServiceConfig
from models import FigmaDesign, FigmaFrame, FigmaComponent, UITestCase, TestSuite
from utils import generate_id, make_http_request

logger = structlog.get_logger()


class UITestGenerator:
    """Generates UI tests from Figma design analysis"""
    
    def __init__(self, config: FigmaServiceConfig):
        self.config = config
    
    async def generate_ui_tests(self, design: FigmaDesign, target_url: str) -> TestSuite:
        """Generate complete UI test suite from Figma design"""
        logger.info("Generating UI tests", 
                   design_name=design.name, 
                   target_url=target_url)
        
        test_suite = TestSuite(
            name=f"UI Tests - {design.name}",
            description=f"Generated UI tests for {design.name} design",
            url=target_url,
            figma_file_key=design.file_key
        )
        
        # Generate tests for each frame
        for frame in design.frames:
            frame_tests = await self._generate_frame_tests(frame, target_url)
            test_suite.ui_tests.extend(frame_tests)
        
        # Generate style consistency tests
        style_tests = await self._generate_style_tests(design, target_url)
        test_suite.ui_tests.extend(style_tests)
        
        # Generate layout tests
        layout_tests = await self._generate_layout_tests(design, target_url)
        test_suite.ui_tests.extend(layout_tests)
        
        logger.info("Generated UI test suite", 
                   total_tests=len(test_suite.ui_tests),
                   frames_processed=len(design.frames))
        
        return test_suite
    
    async def _generate_frame_tests(self, frame: FigmaFrame, target_url: str) -> List[UITestCase]:
        """Generate tests for a specific frame"""
        tests = []
        
        for component in frame.components:
            component_tests = await self._generate_component_tests(component, target_url)
            tests.extend(component_tests)
        
        return tests
    
    async def _generate_component_tests(self, component: FigmaComponent, target_url: str) -> List[UITestCase]:
        """Generate tests for a specific component"""
        tests = []
        
        # Generate CSS selector for component
        selector = self._generate_css_selector(component)
        
        # Element existence test
        tests.append(UITestCase(
            component_name=component.name,
            selector=selector,
            test_type="exists",
            figma_component_id=component.id
        ))
        
        # Visibility test
        tests.append(UITestCase(
            component_name=component.name,
            selector=selector,
            test_type="visible",
            figma_component_id=component.id
        ))
        
        # Text content test (for text components)
        if component.type == "TEXT" and component.characters:
            tests.append(UITestCase(
                component_name=component.name,
                selector=selector,
                test_type="text",
                expected_value=component.characters.strip(),
                figma_component_id=component.id
            ))
        
        # Color tests (for components with fills)
        if component.fills:
            for i, fill in enumerate(component.fills):
                if fill.get("type") == "SOLID":
                    color = self._rgba_to_hex(fill.get("color", {}))
                    if color:
                        tests.append(UITestCase(
                            component_name=f"{component.name}_color_{i}",
                            selector=selector,
                            test_type="style",
                            expected_value=f"background-color:{color}",
                            figma_component_id=component.id
                        ))
        
        # Interactive element tests
        if self._is_interactive_component(component):
            tests.append(UITestCase(
                component_name=f"{component.name}_clickable",
                selector=selector,
                test_type="clickable",
                figma_component_id=component.id
            ))
        
        # Size and position tests (optional, can be enabled)
        if self._should_test_dimensions(component):
            tests.append(UITestCase(
                component_name=f"{component.name}_dimensions",
                selector=selector,
                test_type="dimensions",
                expected_value=f"width:{component.width}px,height:{component.height}px",
                figma_component_id=component.id
            ))
        
        # Recursively test children
        for child in component.children:
            child_tests = await self._generate_component_tests(child, target_url)
            tests.extend(child_tests)
        
        return tests
    
    def _generate_css_selector(self, component: FigmaComponent) -> str:
        """Generate CSS selector for component based on its properties"""
        selectors = []
        
        # Try to generate selector based on component name
        clean_name = self._clean_component_name(component.name)
        
        # Priority order: ID > Class > Tag > Text content > Position
        
        # If name looks like an ID
        if clean_name and not " " in clean_name and len(clean_name) < 30:
            # Try ID selector
            selectors.append(f"#{clean_name}")
            # Try class selector
            selectors.append(f".{clean_name}")
            # Try data attribute
            selectors.append(f"[data-testid='{clean_name}']")
        
        # For text components, try to select by text content
        if component.type == "TEXT" and component.characters:
            text = component.characters.strip()[:50]  # Limit length
            selectors.append(f"*:contains('{text}')")
        
        # For interactive components, try common selectors
        if self._is_button_component(component):
            selectors.extend([
                f"button:contains('{clean_name}')",
                f"[role='button']:contains('{clean_name}')",
                "button",
                "[type='submit']",
                ".btn", ".button"
            ])
        elif self._is_input_component(component):
            selectors.extend([
                f"input[placeholder*='{clean_name}']",
                f"input[name*='{clean_name}']",
                "input[type='text']",
                "input",
                ".form-control"
            ])
        
        # Generic fallback selectors
        selectors.extend([
            f".{clean_name.replace(' ', '-').lower()}",
            f"[aria-label*='{clean_name}']",
            f"[title*='{clean_name}']"
        ])
        
        # Return the most likely selector (first one)
        return selectors[0] if selectors else "*"
    
    def _clean_component_name(self, name: str) -> str:
        """Clean component name for use in selectors"""
        # Remove special characters, keep alphanumeric and common separators
        cleaned = re.sub(r'[^\w\s_-]', '', name)
        # Replace spaces with dashes
        cleaned = re.sub(r'\s+', '-', cleaned.strip())
        return cleaned.lower()
    
    def _is_interactive_component(self, component: FigmaComponent) -> bool:
        """Check if component is interactive (button, link, input, etc.)"""
        return (
            self._is_button_component(component) or
            self._is_input_component(component) or
            "interactive" in component.style.get("component_type", "").lower() or
            any(keyword in component.name.lower() for keyword in [
                "link", "nav", "menu", "tab", "toggle", "switch"
            ])
        )
    
    def _is_button_component(self, component: FigmaComponent) -> bool:
        """Check if component is a button"""
        name = component.name.lower()
        return (
            component.style.get("component_type") == "button" or
            any(keyword in name for keyword in [
                "button", "btn", "cta", "submit", "action", "click"
            ])
        )
    
    def _is_input_component(self, component: FigmaComponent) -> bool:
        """Check if component is an input field"""
        name = component.name.lower()
        return (
            component.style.get("component_type") == "input" or
            any(keyword in name for keyword in [
                "input", "field", "textbox", "search", "form", "email", "password"
            ])
        )
    
    def _should_test_dimensions(self, component: FigmaComponent) -> bool:
        """Determine if we should test component dimensions"""
        # Test dimensions for important layout components
        return (
            component.width > 100 and component.height > 100 or  # Large components
            self._is_interactive_component(component) or  # Interactive elements
            component.type in ["FRAME", "GROUP"]  # Layout containers
        )
    
    async def _generate_style_tests(self, design: FigmaDesign, target_url: str) -> List[UITestCase]:
        """Generate tests for style consistency (colors, fonts, etc.)"""
        tests = []
        
        if not design.styles:
            return tests
        
        # Color consistency tests
        colors = design.styles.get("colors", {})
        primary_colors = sorted(
            colors.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:3]  # Top 3 colors
        
        for color_hex, color_info in primary_colors:
            tests.append(UITestCase(
                component_name=f"primary_color_{color_hex}",
                selector=f"*[style*='{color_hex}'], *[style*='{color_hex.lower()}']",
                test_type="color_exists",
                expected_value=color_hex,
                figma_component_id=f"style_color_{color_hex}"
            ))
        
        # Typography tests
        typography = design.styles.get("typography", {})
        for font_key, font_info in typography.items():
            if font_info.get("usage") == "heading":
                tests.append(UITestCase(
                    component_name=f"heading_font_{font_key}",
                    selector=f"h1, h2, h3, h4, h5, h6, .heading, .title",
                    test_type="font_family",
                    expected_value=font_info["font_family"],
                    figma_component_id=f"style_font_{font_key}"
                ))
        
        return tests
    
    async def _generate_layout_tests(self, design: FigmaDesign, target_url: str) -> List[UITestCase]:
        """Generate tests for layout and responsive behavior"""
        tests = []
        
        # Responsive tests for different viewports
        viewports = [
            {"name": "desktop", "width": 1920, "height": 1080},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "mobile", "width": 375, "height": 667}
        ]
        
        for viewport in viewports:
            # Test that main content is visible in viewport
            tests.append(UITestCase(
                component_name=f"responsive_{viewport['name']}",
                selector="body",
                test_type="viewport_test",
                expected_value=f"{viewport['width']}x{viewport['height']}",
                figma_component_id=f"layout_responsive_{viewport['name']}"
            ))
        
        # Spacing consistency tests
        if design.styles and "spacing" in design.styles:
            common_margins = design.styles["spacing"].get("margins", [])[:3]
            for i, margin in enumerate(common_margins):
                tests.append(UITestCase(
                    component_name=f"margin_consistency_{i}",
                    selector="*",
                    test_type="spacing",
                    expected_value=f"margin:{margin}px",
                    figma_component_id=f"spacing_margin_{i}"
                ))
        
        return tests
    
    def _rgba_to_hex(self, color: Dict[str, float]) -> Optional[str]:
        """Convert RGBA color to hex"""
        try:
            r = int(color.get("r", 0) * 255)
            g = int(color.get("g", 0) * 255) 
            b = int(color.get("b", 0) * 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (KeyError, ValueError):
            return None
    
    async def generate_visual_regression_tests(
        self, 
        design: FigmaDesign, 
        target_url: str
    ) -> List[UITestCase]:
        """Generate visual regression tests by comparing with Figma screenshots"""
        tests = []
        
        for frame in design.frames:
            # Create visual regression test for each frame
            tests.append(UITestCase(
                component_name=f"visual_regression_{frame.name}",
                selector="body",
                test_type="visual_regression",
                expected_value=frame.id,  # Use Figma frame ID as baseline
                figma_component_id=frame.id,
                screenshot_baseline=f"figma_frame_{frame.id}.png"
            ))
        
        return tests
    
    async def optimize_test_suite(self, test_suite: TestSuite) -> TestSuite:
        """Optimize test suite by removing duplicates and prioritizing important tests"""
        logger.info("Optimizing test suite", original_count=len(test_suite.ui_tests))
        
        # Remove duplicate selectors
        seen_selectors = set()
        unique_tests = []
        
        for test in test_suite.ui_tests:
            test_key = f"{test.selector}_{test.test_type}"
            if test_key not in seen_selectors:
                seen_selectors.add(test_key)
                unique_tests.append(test)
        
        test_suite.ui_tests = unique_tests
        
        # Prioritize interactive elements and important components
        test_suite.ui_tests.sort(key=lambda t: (
            -1 if any(keyword in t.component_name.lower() 
                     for keyword in ["button", "input", "form", "nav"]) else 0,
            -1 if t.test_type in ["exists", "visible"] else 0,
            t.component_name.lower()
        ))
        
        logger.info("Optimized test suite", 
                   final_count=len(test_suite.ui_tests),
                   removed=len(test_suite.ui_tests) - len(unique_tests))
        
        return test_suite