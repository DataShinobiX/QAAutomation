"""
UI Component Detector
Identifies and classifies UI components in screenshots using computer vision
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
import structlog
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class DetectedComponent(NamedTuple):
    """Detected UI component"""
    component_type: str
    confidence: float
    bounding_box: Dict[str, int]
    properties: Dict[str, Any]
    center_point: Tuple[int, int]

class ComponentDetectionResult:
    """Result of component detection analysis"""
    def __init__(
        self,
        image_path: str,
        components: List[DetectedComponent],
        analysis_metadata: Dict[str, Any]
    ):
        self.image_path = image_path
        self.components = components
        self.analysis_metadata = analysis_metadata
        self.detected_at = datetime.utcnow()
        
    def get_components_by_type(self, component_type: str) -> List[DetectedComponent]:
        """Get all components of a specific type"""
        return [comp for comp in self.components if comp.component_type == component_type]
    
    def get_component_count(self) -> Dict[str, int]:
        """Get count of each component type"""
        counts = {}
        for comp in self.components:
            counts[comp.component_type] = counts.get(comp.component_type, 0) + 1
        return counts

class ComponentDetector:
    """Advanced UI component detection using computer vision techniques"""
    
    def __init__(self):
        # Initialize component templates and classifiers
        self.component_templates = self._load_component_templates()
        
        # Initialize cascade classifiers if available
        self.button_cascade = self._load_cascade_classifier('button')
        self.text_cascade = self._load_cascade_classifier('text')
        
        logger.info("Component Detector initialized",
                   templates_loaded=len(self.component_templates),
                   cascades_available=bool(self.button_cascade or self.text_cascade))
    
    def _load_component_templates(self) -> Dict[str, List[np.ndarray]]:
        """Load component templates for template matching"""
        templates = {
            'button': [],
            'input': [],
            'checkbox': [],
            'radio': [],
            'dropdown': [],
            'icon': [],
            'link': [],
            'image': []
        }
        
        # In a real implementation, these would be loaded from template files
        # For now, we'll use procedurally generated templates
        
        # Button templates (various sizes and styles)
        for width, height in [(100, 30), (120, 40), (80, 25), (150, 45)]:
            button_template = self._create_button_template(width, height)
            templates['button'].append(button_template)
        
        # Input field templates
        for width, height in [(200, 30), (150, 25), (300, 35), (100, 20)]:
            input_template = self._create_input_template(width, height)
            templates['input'].append(input_template)
        
        # Checkbox templates
        for size in [15, 18, 20, 25]:
            checkbox_template = self._create_checkbox_template(size)
            templates['checkbox'].append(checkbox_template)
        
        return templates
    
    def _create_button_template(self, width: int, height: int) -> np.ndarray:
        """Create a generic button template"""
        template = np.ones((height, width, 3), dtype=np.uint8) * 240  # Light gray
        
        # Add border
        cv2.rectangle(template, (0, 0), (width-1, height-1), (100, 100, 100), 1)
        
        # Add subtle gradient effect
        for i in range(height):
            intensity = int(240 - (i * 20 / height))
            template[i, :] = [intensity, intensity, intensity]
        
        return cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    def _create_input_template(self, width: int, height: int) -> np.ndarray:
        """Create a generic input field template"""
        template = np.ones((height, width, 3), dtype=np.uint8) * 255  # White
        
        # Add border
        cv2.rectangle(template, (0, 0), (width-1, height-1), (150, 150, 150), 1)
        
        return cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    def _create_checkbox_template(self, size: int) -> np.ndarray:
        """Create a generic checkbox template"""
        template = np.ones((size, size, 3), dtype=np.uint8) * 255  # White
        
        # Add border
        cv2.rectangle(template, (0, 0), (size-1, size-1), (100, 100, 100), 1)
        
        return cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    def _load_cascade_classifier(self, component_type: str) -> Optional[cv2.CascadeClassifier]:
        """Load Haar cascade classifier for component detection"""
        # In a real implementation, you would load pre-trained cascade files
        # For now, we'll return None and use other detection methods
        return None
    
    async def detect_components(
        self,
        image_path: str,
        component_types: Optional[List[str]] = None,
        confidence_threshold: float = None
    ) -> ComponentDetectionResult:
        """
        Detect UI components in an image
        
        Args:
            image_path: Path to image file
            component_types: List of component types to detect (None for all)
            confidence_threshold: Minimum confidence threshold
        """
        logger.info("Starting component detection", 
                   image_path=image_path,
                   component_types=component_types)
        
        if confidence_threshold is None:
            confidence_threshold = config.component_detection_confidence
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            detected_components = []
            
            # Detect different types of components
            if not component_types or 'button' in component_types:
                buttons = await self._detect_buttons(image, gray)
                detected_components.extend(buttons)
            
            if not component_types or 'input' in component_types:
                inputs = await self._detect_input_fields(image, gray)
                detected_components.extend(inputs)
            
            if not component_types or 'text' in component_types:
                texts = await self._detect_text_elements(image, gray)
                detected_components.extend(texts)
            
            if not component_types or 'image' in component_types:
                images = await self._detect_images(image, gray)
                detected_components.extend(images)
            
            if not component_types or 'icon' in component_types:
                icons = await self._detect_icons(image, gray)
                detected_components.extend(icons)
            
            if not component_types or 'checkbox' in component_types:
                checkboxes = await self._detect_checkboxes(image, gray)
                detected_components.extend(checkboxes)
            
            if not component_types or 'dropdown' in component_types:
                dropdowns = await self._detect_dropdowns(image, gray)
                detected_components.extend(dropdowns)
            
            # Filter by confidence threshold
            filtered_components = [
                comp for comp in detected_components 
                if comp.confidence >= confidence_threshold
            ]
            
            # Remove overlapping components (non-maximum suppression)
            final_components = self._apply_non_maximum_suppression(filtered_components)
            
            analysis_metadata = {
                "image_size": image.shape[:2],
                "total_detected": len(detected_components),
                "after_filtering": len(filtered_components),
                "final_count": len(final_components),
                "confidence_threshold": confidence_threshold,
                "detection_methods": ["template_matching", "contour_analysis", "edge_detection"]
            }
            
            logger.info("Component detection completed",
                       image_path=image_path,
                       components_detected=len(final_components),
                       component_types=[comp.component_type for comp in final_components])
            
            return ComponentDetectionResult(
                image_path=image_path,
                components=final_components,
                analysis_metadata=analysis_metadata
            )
            
        except Exception as e:
            logger.error("Component detection failed", 
                        image_path=image_path, 
                        error=str(e))
            return ComponentDetectionResult(
                image_path=image_path,
                components=[],
                analysis_metadata={"error": str(e)}
            )
    
    async def _detect_buttons(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect button components using multiple techniques"""
        buttons = []
        
        # Method 1: Template matching
        for template in self.component_templates['button']:
            matches = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(matches >= 0.6)
            
            for pt in zip(*locations[::-1]):
                confidence = matches[pt[1], pt[0]]
                h, w = template.shape
                
                buttons.append(DetectedComponent(
                    component_type='button',
                    confidence=float(confidence),
                    bounding_box={'x': int(pt[0]), 'y': int(pt[1]), 'width': w, 'height': h},
                    properties={'detection_method': 'template_matching'},
                    center_point=(int(pt[0] + w/2), int(pt[1] + h/2))
                ))
        
        # Method 2: Contour-based detection
        # Find rectangular contours that might be buttons
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular
            if len(approx) >= 4:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                area = cv2.contourArea(contour)
                
                # Button heuristics: reasonable size, aspect ratio, and area
                if (20 <= w <= 300 and 15 <= h <= 80 and 
                    1.5 <= aspect_ratio <= 6.0 and area > 300):
                    
                    # Check if the region looks button-like
                    button_region = gray[y:y+h, x:x+w]
                    if self._is_button_like_region(button_region):
                        confidence = min(0.8, area / 10000)  # Confidence based on size
                        
                        buttons.append(DetectedComponent(
                            component_type='button',
                            confidence=confidence,
                            bounding_box={'x': x, 'y': y, 'width': w, 'height': h},
                            properties={
                                'detection_method': 'contour_analysis',
                                'aspect_ratio': aspect_ratio,
                                'area': int(area)
                            },
                            center_point=(x + w//2, y + h//2)
                        ))
        
        return buttons
    
    async def _detect_input_fields(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect input field components"""
        inputs = []
        
        # Method 1: Template matching
        for template in self.component_templates['input']:
            matches = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(matches >= 0.6)
            
            for pt in zip(*locations[::-1]):
                confidence = matches[pt[1], pt[0]]
                h, w = template.shape
                
                inputs.append(DetectedComponent(
                    component_type='input',
                    confidence=float(confidence),
                    bounding_box={'x': int(pt[0]), 'y': int(pt[1]), 'width': w, 'height': h},
                    properties={'detection_method': 'template_matching'},
                    center_point=(int(pt[0] + w/2), int(pt[1] + h/2))
                ))
        
        # Method 2: Edge-based detection for rectangular input fields
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            area = cv2.contourArea(contour)
            
            # Input field heuristics: wide and not too tall
            if (50 <= w <= 500 and 15 <= h <= 50 and 
                aspect_ratio >= 3.0 and area > 400):
                
                # Check if region looks like an input field
                input_region = gray[y:y+h, x:x+w]
                if self._is_input_like_region(input_region):
                    confidence = min(0.7, area / 15000)
                    
                    inputs.append(DetectedComponent(
                        component_type='input',
                        confidence=confidence,
                        bounding_box={'x': x, 'y': y, 'width': w, 'height': h},
                        properties={
                            'detection_method': 'edge_analysis',
                            'aspect_ratio': aspect_ratio,
                            'area': int(area)
                        },
                        center_point=(x + w//2, y + h//2)
                    ))
        
        return inputs
    
    async def _detect_text_elements(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect text elements"""
        texts = []
        
        # Use MSER (Maximally Stable Extremal Regions) to detect text regions
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        for region in regions:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
            
            # Filter by text-like properties
            aspect_ratio = w / h
            area = len(region)
            
            if (10 <= w <= 800 and 8 <= h <= 100 and 
                0.1 <= aspect_ratio <= 15.0 and 50 <= area <= 10000):
                
                confidence = min(0.6, area / 5000)
                
                texts.append(DetectedComponent(
                    component_type='text',
                    confidence=confidence,
                    bounding_box={'x': x, 'y': y, 'width': w, 'height': h},
                    properties={
                        'detection_method': 'mser',
                        'aspect_ratio': aspect_ratio,
                        'area': int(area)
                    },
                    center_point=(x + w//2, y + h//2)
                ))
        
        return texts
    
    async def _detect_images(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect image elements"""
        images = []
        
        # Detect rectangular regions that might contain images
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Image heuristics: larger rectangular areas
            if (w >= 50 and h >= 50 and area >= 2500):
                # Check if region has image-like properties (texture, variance)
                image_region = gray[y:y+h, x:x+w]
                if self._is_image_like_region(image_region):
                    confidence = min(0.7, area / 50000)
                    
                    images.append(DetectedComponent(
                        component_type='image',
                        confidence=confidence,
                        bounding_box={'x': x, 'y': y, 'width': w, 'height': h},
                        properties={
                            'detection_method': 'texture_analysis',
                            'area': int(area)
                        },
                        center_point=(x + w//2, y + h//2)
                    ))
        
        return images
    
    async def _detect_icons(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect icon elements"""
        icons = []
        
        # Icons are typically small, square-ish elements with high contrast
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            area = cv2.contourArea(contour)
            
            # Icon heuristics: small, roughly square
            if (10 <= w <= 100 and 10 <= h <= 100 and 
                0.5 <= aspect_ratio <= 2.0 and 100 <= area <= 5000):
                
                confidence = 0.5  # Icons are harder to detect reliably
                
                icons.append(DetectedComponent(
                    component_type='icon',
                    confidence=confidence,
                    bounding_box={'x': x, 'y': y, 'width': w, 'height': h},
                    properties={
                        'detection_method': 'size_analysis',
                        'aspect_ratio': aspect_ratio,
                        'area': int(area)
                    },
                    center_point=(x + w//2, y + h//2)
                ))
        
        return icons
    
    async def _detect_checkboxes(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect checkbox elements"""
        checkboxes = []
        
        # Template matching for checkboxes
        for template in self.component_templates['checkbox']:
            matches = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(matches >= 0.7)
            
            for pt in zip(*locations[::-1]):
                confidence = matches[pt[1], pt[0]]
                h, w = template.shape
                
                checkboxes.append(DetectedComponent(
                    component_type='checkbox',
                    confidence=float(confidence),
                    bounding_box={'x': int(pt[0]), 'y': int(pt[1]), 'width': w, 'height': h},
                    properties={'detection_method': 'template_matching'},
                    center_point=(int(pt[0] + w/2), int(pt[1] + h/2))
                ))
        
        return checkboxes
    
    async def _detect_dropdowns(self, image: np.ndarray, gray: np.ndarray) -> List[DetectedComponent]:
        """Detect dropdown elements"""
        dropdowns = []
        
        # Look for rectangles with dropdown arrow indicators
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            area = cv2.contourArea(contour)
            
            # Dropdown heuristics: wider than tall, medium size
            if (80 <= w <= 300 and 20 <= h <= 50 and 
                aspect_ratio >= 2.5 and area > 800):
                
                # Look for dropdown arrow in the right side of the region
                arrow_region = gray[y:y+h, x+w-30:x+w]
                if self._has_dropdown_arrow(arrow_region):
                    confidence = 0.6
                    
                    dropdowns.append(DetectedComponent(
                        component_type='dropdown',
                        confidence=confidence,
                        bounding_box={'x': x, 'y': y, 'width': w, 'height': h},
                        properties={
                            'detection_method': 'arrow_detection',
                            'aspect_ratio': aspect_ratio
                        },
                        center_point=(x + w//2, y + h//2)
                    ))
        
        return dropdowns
    
    def _is_button_like_region(self, region: np.ndarray) -> bool:
        """Check if a region looks like a button"""
        if region.size == 0:
            return False
        
        # Buttons typically have uniform color and clear borders
        std_dev = np.std(region)
        mean_intensity = np.mean(region)
        
        # Button heuristics: not too much variation, not too dark/light
        return 5 < std_dev < 50 and 50 < mean_intensity < 200
    
    def _is_input_like_region(self, region: np.ndarray) -> bool:
        """Check if a region looks like an input field"""
        if region.size == 0:
            return False
        
        # Input fields typically have light background with borders
        mean_intensity = np.mean(region)
        border_mean = np.mean([
            np.mean(region[0, :]),  # top
            np.mean(region[-1, :]),  # bottom
            np.mean(region[:, 0]),  # left
            np.mean(region[:, -1])  # right
        ])
        
        # Input heuristics: light interior, darker borders
        return mean_intensity > 180 and border_mean < mean_intensity - 20
    
    def _is_image_like_region(self, region: np.ndarray) -> bool:
        """Check if a region looks like an image"""
        if region.size == 0:
            return False
        
        # Images typically have high texture variance
        std_dev = np.std(region)
        
        # Use Laplacian to detect edges/texture
        laplacian_var = cv2.Laplacian(region, cv2.CV_64F).var()
        
        # Image heuristics: high texture variance
        return std_dev > 30 and laplacian_var > 500
    
    def _has_dropdown_arrow(self, region: np.ndarray) -> bool:
        """Check if a region contains a dropdown arrow"""
        if region.size == 0:
            return False
        
        # Simple heuristic: look for triangular patterns
        # This could be enhanced with template matching for common arrow shapes
        edges = cv2.Canny(region, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 10 <= area <= 200:  # Small triangular shapes
                # Check if contour is roughly triangular
                epsilon = 0.1 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) == 3:  # Triangle
                    return True
        
        return False
    
    def _apply_non_maximum_suppression(
        self, 
        components: List[DetectedComponent],
        overlap_threshold: float = 0.5
    ) -> List[DetectedComponent]:
        """Remove overlapping component detections"""
        if not components:
            return components
        
        # Sort by confidence (highest first)
        sorted_components = sorted(components, key=lambda x: x.confidence, reverse=True)
        
        final_components = []
        
        for component in sorted_components:
            # Check if this component overlaps significantly with any already selected
            overlaps = False
            
            for selected in final_components:
                if self._calculate_overlap(component, selected) > overlap_threshold:
                    overlaps = True
                    break
            
            if not overlaps:
                final_components.append(component)
        
        return final_components
    
    def _calculate_overlap(self, comp1: DetectedComponent, comp2: DetectedComponent) -> float:
        """Calculate overlap ratio between two components"""
        bbox1 = comp1.bounding_box
        bbox2 = comp2.bounding_box
        
        # Calculate intersection
        x1 = max(bbox1['x'], bbox2['x'])
        y1 = max(bbox1['y'], bbox2['y'])
        x2 = min(bbox1['x'] + bbox1['width'], bbox2['x'] + bbox2['width'])
        y2 = min(bbox1['y'] + bbox1['height'], bbox2['y'] + bbox2['height'])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection_area = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        area1 = bbox1['width'] * bbox1['height']
        area2 = bbox2['width'] * bbox2['height']
        union_area = area1 + area2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0