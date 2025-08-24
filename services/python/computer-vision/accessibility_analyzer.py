"""
Accessibility Analyzer
Advanced accessibility analysis for UI elements and compliance checking
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import structlog
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageStat
import colorsys
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class AccessibilityIssue:
    """Represents an accessibility issue"""
    def __init__(
        self,
        issue_type: str,
        severity: str,
        message: str,
        element: Dict[str, Any],
        wcag_guideline: str,
        recommendation: str = ""
    ):
        self.issue_type = issue_type
        self.severity = severity  # critical, warning, info
        self.message = message
        self.element = element
        self.wcag_guideline = wcag_guideline
        self.recommendation = recommendation
        self.detected_at = datetime.utcnow()

class ColorAnalyzer:
    """Analyze colors for accessibility compliance"""
    
    @staticmethod
    def rgb_to_luminance(rgb: Tuple[int, int, int]) -> float:
        """Convert RGB to relative luminance for contrast calculations"""
        def linearize_rgb(c):
            c = c / 255.0
            if c <= 0.03928:
                return c / 12.92
            else:
                return pow((c + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        r_lin = linearize_rgb(r)
        g_lin = linearize_rgb(g)
        b_lin = linearize_rgb(b)
        
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    
    @staticmethod
    def calculate_contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate WCAG contrast ratio between two colors"""
        lum1 = ColorAnalyzer.rgb_to_luminance(color1)
        lum2 = ColorAnalyzer.rgb_to_luminance(color2)
        
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    @staticmethod
    def get_dominant_colors(image_region: np.ndarray, num_colors: int = 2) -> List[Tuple[int, int, int]]:
        """Get dominant colors from an image region"""
        # Convert to PIL Image for easier processing
        pil_img = Image.fromarray(cv2.cvtColor(image_region, cv2.COLOR_BGR2RGB))
        
        # Reduce image size for faster processing
        pil_img.thumbnail((50, 50))
        
        # Convert to indexed color mode to get dominant colors
        pil_img = pil_img.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
        
        # Get the color palette
        palette = pil_img.getpalette()
        
        # Convert palette to RGB tuples
        colors = []
        for i in range(num_colors):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            colors.append((r, g, b))
        
        return colors
    
    def analyze_text_contrast(
        self, 
        text_region: np.ndarray, 
        background_region: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Analyze text contrast against background"""
        if background_region is None:
            background_region = text_region
        
        # Get dominant colors
        text_colors = self.get_dominant_colors(text_region, 2)
        bg_colors = self.get_dominant_colors(background_region, 2)
        
        # Calculate contrast ratios between text and background colors
        max_contrast = 0
        best_text_color = text_colors[0]
        best_bg_color = bg_colors[0]
        
        for text_color in text_colors:
            for bg_color in bg_colors:
                contrast = self.calculate_contrast_ratio(text_color, bg_color)
                if contrast > max_contrast:
                    max_contrast = contrast
                    best_text_color = text_color
                    best_bg_color = bg_color
        
        return {
            "contrast_ratio": max_contrast,
            "text_color": best_text_color,
            "background_color": best_bg_color,
            "wcag_aa_pass": max_contrast >= config.min_contrast_ratio_aa,
            "wcag_aaa_pass": max_contrast >= config.min_contrast_ratio_aaa
        }

class AccessibilityAnalyzer:
    """Comprehensive accessibility analysis for UI elements"""
    
    def __init__(self):
        self.color_analyzer = ColorAnalyzer()
        logger.info("Accessibility Analyzer initialized")
    
    async def analyze_image_accessibility(
        self,
        image_path: str,
        text_elements: List[Dict[str, Any]] = None,
        ui_components: List[Dict[str, Any]] = None,
        wcag_level: str = "AA"
    ) -> Dict[str, Any]:
        """
        Comprehensive accessibility analysis of an image
        
        Args:
            image_path: Path to image file
            text_elements: List of detected text elements with bounding boxes
            ui_components: List of detected UI components
            wcag_level: WCAG compliance level (AA or AAA)
        """
        logger.info("Starting accessibility analysis",
                   image_path=image_path,
                   wcag_level=wcag_level)
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            issues = []
            recommendations = []
            
            # Analyze text elements
            if text_elements:
                text_issues = await self._analyze_text_accessibility(
                    image, text_elements, wcag_level
                )
                issues.extend(text_issues)
            
            # Analyze UI components
            if ui_components:
                component_issues = await self._analyze_component_accessibility(
                    image, ui_components, wcag_level
                )
                issues.extend(component_issues)
            
            # Overall image analysis
            overall_issues = await self._analyze_overall_accessibility(image, wcag_level)
            issues.extend(overall_issues)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issues, wcag_level)
            
            # Calculate accessibility score
            score = self._calculate_accessibility_score(issues, wcag_level)
            
            result = {
                "image_path": image_path,
                "wcag_level": wcag_level,
                "accessibility_score": score,
                "total_issues": len(issues),
                "issues_by_severity": self._categorize_issues_by_severity(issues),
                "issues": [self._issue_to_dict(issue) for issue in issues],
                "recommendations": recommendations,
                "analysis_metadata": {
                    "image_size": image.shape[:2],
                    "text_elements_analyzed": len(text_elements) if text_elements else 0,
                    "components_analyzed": len(ui_components) if ui_components else 0,
                    "wcag_guidelines_checked": self._get_checked_guidelines()
                },
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Accessibility analysis completed",
                       score=score,
                       total_issues=len(issues),
                       wcag_level=wcag_level)
            
            return result
            
        except Exception as e:
            logger.error("Accessibility analysis failed",
                        image_path=image_path,
                        error=str(e))
            raise
    
    async def _analyze_text_accessibility(
        self,
        image: np.ndarray,
        text_elements: List[Dict[str, Any]],
        wcag_level: str
    ) -> List[AccessibilityIssue]:
        """Analyze text elements for accessibility issues"""
        issues = []
        
        for text_element in text_elements:
            bbox = text_element.get("bounding_box", {})
            text = text_element.get("text", "")
            
            if not bbox or not text:
                continue
            
            x, y, width, height = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
            
            # Extract text region from image
            text_region = image[y:y+height, x:x+width]
            if text_region.size == 0:
                continue
            
            # 1. Text size analysis
            estimated_font_size = height * 0.75  # Rough estimation
            if estimated_font_size < config.min_text_size_pt:
                issues.append(AccessibilityIssue(
                    issue_type="text_size",
                    severity="warning",
                    message=f"Text may be too small: ~{estimated_font_size:.1f}pt (minimum {config.min_text_size_pt}pt)",
                    element=text_element,
                    wcag_guideline="1.4.4 Resize text",
                    recommendation=f"Increase font size to at least {config.min_text_size_pt}pt"
                ))
            
            # 2. Contrast analysis
            # Get surrounding area for background analysis
            bg_padding = 10
            bg_x1 = max(0, x - bg_padding)
            bg_y1 = max(0, y - bg_padding)
            bg_x2 = min(image.shape[1], x + width + bg_padding)
            bg_y2 = min(image.shape[0], y + height + bg_padding)
            
            background_region = image[bg_y1:bg_y2, bg_x1:bg_x2]
            
            contrast_result = self.color_analyzer.analyze_text_contrast(
                text_region, background_region
            )
            
            min_contrast = (config.min_contrast_ratio_aaa if wcag_level == "AAA" 
                          else config.min_contrast_ratio_aa)
            
            if contrast_result["contrast_ratio"] < min_contrast:
                issues.append(AccessibilityIssue(
                    issue_type="contrast",
                    severity="critical" if contrast_result["contrast_ratio"] < 3.0 else "warning",
                    message=f"Insufficient contrast: {contrast_result['contrast_ratio']:.2f} (minimum {min_contrast})",
                    element={
                        **text_element,
                        "contrast_analysis": contrast_result
                    },
                    wcag_guideline="1.4.3 Contrast (Minimum)" if wcag_level == "AA" else "1.4.6 Contrast (Enhanced)",
                    recommendation=f"Increase contrast to at least {min_contrast}:1"
                ))
            
            # 3. Text length analysis (for readability)
            if len(text) > 120:  # Very long text might be hard to read
                issues.append(AccessibilityIssue(
                    issue_type="readability",
                    severity="info",
                    message=f"Very long text block ({len(text)} characters) may be difficult to read",
                    element=text_element,
                    wcag_guideline="3.1.5 Reading Level",
                    recommendation="Consider breaking long text into shorter paragraphs"
                ))
        
        return issues
    
    async def _analyze_component_accessibility(
        self,
        image: np.ndarray,
        ui_components: List[Dict[str, Any]],
        wcag_level: str
    ) -> List[AccessibilityIssue]:
        """Analyze UI components for accessibility issues"""
        issues = []
        
        for component in ui_components:
            comp_type = component.get("type", "")
            bbox = component.get("bounding_box", {})
            
            if not bbox:
                continue
            
            width = bbox["width"]
            height = bbox["height"]
            
            # 1. Touch target size analysis
            if comp_type in ["button", "checkbox", "radio", "dropdown"]:
                min_touch_size = 44  # WCAG recommendation for touch targets
                
                if width < min_touch_size or height < min_touch_size:
                    issues.append(AccessibilityIssue(
                        issue_type="touch_target",
                        severity="warning",
                        message=f"{comp_type} too small for touch: {width}x{height}px (minimum {min_touch_size}x{min_touch_size}px)",
                        element=component,
                        wcag_guideline="2.5.5 Target Size",
                        recommendation=f"Increase {comp_type} size to at least {min_touch_size}x{min_touch_size}px"
                    ))
            
            # 2. Component spacing analysis
            # This would require analyzing distances between components
            # For now, we'll check if components are too close to screen edges
            image_height, image_width = image.shape[:2]
            margin_threshold = 16  # Minimum margin from screen edge
            
            x, y = bbox["x"], bbox["y"]
            if (x < margin_threshold or y < margin_threshold or 
                x + width > image_width - margin_threshold or 
                y + height > image_height - margin_threshold):
                
                issues.append(AccessibilityIssue(
                    issue_type="spacing",
                    severity="info",
                    message=f"{comp_type} too close to screen edge",
                    element=component,
                    wcag_guideline="1.4.4 Resize text",
                    recommendation="Provide adequate spacing around interactive elements"
                ))
            
            # 3. Component visibility analysis
            if comp_type in ["button", "input"] and (width < 20 or height < 10):
                issues.append(AccessibilityIssue(
                    issue_type="visibility",
                    severity="warning",
                    message=f"{comp_type} may be too small to be easily visible",
                    element=component,
                    wcag_guideline="1.4.3 Contrast (Minimum)",
                    recommendation="Ensure components are large enough to be easily seen and interacted with"
                ))
        
        return issues
    
    async def _analyze_overall_accessibility(
        self,
        image: np.ndarray,
        wcag_level: str
    ) -> List[AccessibilityIssue]:
        """Analyze overall image accessibility characteristics"""
        issues = []
        
        # 1. Overall image contrast and brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Very low contrast (flat image) might indicate accessibility issues
        if std_brightness < 20:  # Very low standard deviation
            issues.append(AccessibilityIssue(
                issue_type="overall_contrast",
                severity="info",
                message=f"Low overall image contrast (std: {std_brightness:.1f})",
                element={"image_stats": {"mean_brightness": float(mean_brightness), "std_brightness": float(std_brightness)}},
                wcag_guideline="1.4.3 Contrast (Minimum)",
                recommendation="Ensure sufficient contrast throughout the interface"
            ))
        
        # 2. Color dependency analysis
        # Convert to HSV to analyze color usage
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        mean_saturation = np.mean(saturation)
        
        # High saturation might indicate over-reliance on color
        if mean_saturation > 150:  # High saturation
            issues.append(AccessibilityIssue(
                issue_type="color_dependency",
                severity="info",
                message="Interface may rely heavily on color to convey information",
                element={"color_stats": {"mean_saturation": float(mean_saturation)}},
                wcag_guideline="1.4.1 Use of Color",
                recommendation="Ensure information is not conveyed by color alone"
            ))
        
        return issues
    
    def _generate_recommendations(self, issues: List[AccessibilityIssue], wcag_level: str) -> List[str]:
        """Generate actionable recommendations based on issues found"""
        recommendations = []
        
        issue_types = set(issue.issue_type for issue in issues)
        
        if "contrast" in issue_types:
            recommendations.append("Review and improve color contrast ratios throughout the interface")
        
        if "text_size" in issue_types:
            recommendations.append("Increase font sizes to meet minimum accessibility standards")
        
        if "touch_target" in issue_types:
            recommendations.append("Increase size of interactive elements to meet touch target guidelines")
        
        if "spacing" in issue_types:
            recommendations.append("Improve spacing and layout to enhance usability")
        
        if "color_dependency" in issue_types:
            recommendations.append("Add non-color indicators (icons, text, patterns) to supplement color-coded information")
        
        # General recommendations
        recommendations.append(f"Ensure compliance with WCAG {wcag_level} accessibility guidelines")
        recommendations.append("Test with assistive technologies and real users with disabilities")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_accessibility_score(self, issues: List[AccessibilityIssue], wcag_level: str) -> float:
        """Calculate overall accessibility score (0-1)"""
        if not issues:
            return 1.0
        
        # Weight issues by severity
        severity_weights = {
            "critical": 0.3,
            "warning": 0.1,
            "info": 0.05
        }
        
        total_penalty = sum(severity_weights.get(issue.severity, 0.05) for issue in issues)
        
        # Cap the penalty at 0.9 (minimum score of 0.1)
        total_penalty = min(total_penalty, 0.9)
        
        return max(0.1, 1.0 - total_penalty)
    
    def _categorize_issues_by_severity(self, issues: List[AccessibilityIssue]) -> Dict[str, int]:
        """Categorize issues by severity"""
        categories = {"critical": 0, "warning": 0, "info": 0}
        
        for issue in issues:
            categories[issue.severity] = categories.get(issue.severity, 0) + 1
        
        return categories
    
    def _issue_to_dict(self, issue: AccessibilityIssue) -> Dict[str, Any]:
        """Convert AccessibilityIssue to dictionary"""
        return {
            "type": issue.issue_type,
            "severity": issue.severity,
            "message": issue.message,
            "element": issue.element,
            "wcag_guideline": issue.wcag_guideline,
            "recommendation": issue.recommendation,
            "detected_at": issue.detected_at.isoformat()
        }
    
    def _get_checked_guidelines(self) -> List[str]:
        """Get list of WCAG guidelines checked by this analyzer"""
        return [
            "1.4.1 Use of Color",
            "1.4.3 Contrast (Minimum)",
            "1.4.4 Resize text",
            "1.4.6 Contrast (Enhanced)",
            "2.5.5 Target Size",
            "3.1.5 Reading Level"
        ]