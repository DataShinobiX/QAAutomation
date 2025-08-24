"""
Visual Comparator
Advanced visual comparison for regression testing and difference detection
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import structlog
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageDraw
from skimage.metrics import structural_similarity as ssim
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class VisualDifference:
    """Represents a visual difference between two images"""
    def __init__(
        self,
        difference_type: str,
        region: Dict[str, int],
        severity: str,
        description: str,
        confidence: float = 0.0
    ):
        self.difference_type = difference_type
        self.region = region  # x, y, width, height
        self.severity = severity  # critical, major, minor
        self.description = description
        self.confidence = confidence
        self.detected_at = datetime.utcnow()

class VisualComparisonResult:
    """Result of visual comparison analysis"""
    def __init__(
        self,
        image1_path: str,
        image2_path: str,
        similarity_score: float,
        differences: List[VisualDifference],
        comparison_metadata: Dict[str, Any]
    ):
        self.image1_path = image1_path
        self.image2_path = image2_path
        self.similarity_score = similarity_score
        self.differences = differences
        self.comparison_metadata = comparison_metadata
        self.compared_at = datetime.utcnow()
    
    def get_differences_by_type(self, diff_type: str) -> List[VisualDifference]:
        """Get differences of a specific type"""
        return [diff for diff in self.differences if diff.difference_type == diff_type]
    
    def get_differences_by_severity(self, severity: str) -> List[VisualDifference]:
        """Get differences by severity"""
        return [diff for diff in self.differences if diff.severity == severity]

class VisualComparator:
    """Advanced visual comparison for UI regression testing"""
    
    def __init__(self):
        self.similarity_threshold = config.visual_similarity_threshold
        self.pixel_threshold = config.pixel_difference_threshold
        self.ignore_minor = config.ignore_minor_changes
        
        logger.info("Visual Comparator initialized",
                   similarity_threshold=self.similarity_threshold,
                   pixel_threshold=self.pixel_threshold)
    
    async def compare_images(
        self,
        image1_path: str,
        image2_path: str,
        comparison_type: str = "full",
        ignore_regions: List[Dict[str, int]] = None,
        custom_threshold: float = None
    ) -> VisualComparisonResult:
        """
        Compare two images and detect differences
        
        Args:
            image1_path: Path to reference image
            image2_path: Path to comparison image
            comparison_type: Type of comparison ('full', 'layout', 'color', 'text')
            ignore_regions: Regions to ignore during comparison
            custom_threshold: Custom similarity threshold
        """
        logger.info("Starting visual comparison",
                   image1=image1_path,
                   image2=image2_path,
                   comparison_type=comparison_type)
        
        try:
            # Load images
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            if img1 is None or img2 is None:
                raise ValueError(f"Could not load images: {image1_path}, {image2_path}")
            
            # Resize images to same dimensions if needed
            img1, img2 = self._normalize_images(img1, img2)
            
            # Apply ignore regions if specified
            if ignore_regions:
                img1, img2 = self._apply_ignore_regions(img1, img2, ignore_regions)
            
            differences = []
            similarity_score = 0.0
            
            # Perform different types of comparison
            if comparison_type in ["full", "structural"]:
                structural_result = await self._structural_comparison(img1, img2)
                differences.extend(structural_result["differences"])
                similarity_score = max(similarity_score, structural_result["similarity"])
            
            if comparison_type in ["full", "pixel"]:
                pixel_result = await self._pixel_level_comparison(img1, img2)
                differences.extend(pixel_result["differences"])
                similarity_score = max(similarity_score, pixel_result["similarity"])
            
            if comparison_type in ["full", "color"]:
                color_result = await self._color_comparison(img1, img2)
                differences.extend(color_result["differences"])
            
            if comparison_type in ["full", "layout"]:
                layout_result = await self._layout_comparison(img1, img2)
                differences.extend(layout_result["differences"])
            
            if comparison_type in ["full", "text"]:
                text_result = await self._text_region_comparison(img1, img2)
                differences.extend(text_result["differences"])
            
            # Filter minor differences if configured
            if self.ignore_minor:
                differences = self._filter_minor_differences(differences)
            
            # Sort differences by severity and confidence
            differences = sorted(differences, key=lambda d: (
                {"critical": 0, "major": 1, "minor": 2}[d.severity],
                -d.confidence
            ))
            
            comparison_metadata = {
                "comparison_type": comparison_type,
                "image1_size": img1.shape[:2],
                "image2_size": img2.shape[:2],
                "total_differences": len(differences),
                "ignore_regions_applied": len(ignore_regions) if ignore_regions else 0,
                "similarity_threshold_used": custom_threshold or self.similarity_threshold,
                "comparison_methods": self._get_comparison_methods(comparison_type)
            }
            
            logger.info("Visual comparison completed",
                       similarity_score=similarity_score,
                       differences_found=len(differences),
                       comparison_type=comparison_type)
            
            return VisualComparisonResult(
                image1_path=image1_path,
                image2_path=image2_path,
                similarity_score=similarity_score,
                differences=differences,
                comparison_metadata=comparison_metadata
            )
            
        except Exception as e:
            logger.error("Visual comparison failed",
                        image1=image1_path,
                        image2=image2_path,
                        error=str(e))
            raise
    
    def _normalize_images(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Normalize images to same dimensions"""
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        if h1 != h2 or w1 != w2:
            # Resize to the larger dimensions
            target_h = max(h1, h2)
            target_w = max(w1, w2)
            
            img1_resized = cv2.resize(img1, (target_w, target_h))
            img2_resized = cv2.resize(img2, (target_w, target_h))
            
            logger.info("Images resized for comparison",
                       original_sizes=[(h1, w1), (h2, w2)],
                       target_size=(target_h, target_w))
            
            return img1_resized, img2_resized
        
        return img1, img2
    
    def _apply_ignore_regions(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        ignore_regions: List[Dict[str, int]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Apply ignore regions by masking them out"""
        img1_masked = img1.copy()
        img2_masked = img2.copy()
        
        for region in ignore_regions:
            x, y, w, h = region["x"], region["y"], region["width"], region["height"]
            
            # Fill ignore regions with average color to minimize impact
            avg_color1 = np.mean(img1[y:y+h, x:x+w], axis=(0, 1))
            avg_color2 = np.mean(img2[y:y+h, x:x+w], axis=(0, 1))
            
            img1_masked[y:y+h, x:x+w] = avg_color1
            img2_masked[y:y+h, x:x+w] = avg_color2
        
        return img1_masked, img2_masked
    
    async def _structural_comparison(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Perform structural similarity comparison"""
        differences = []
        
        # Convert to grayscale for SSIM
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Calculate SSIM
        similarity, diff_image = ssim(gray1, gray2, full=True)
        
        # Find regions with significant structural differences
        diff_image = (diff_image * 255).astype(np.uint8)
        diff_threshold = 50
        
        # Find contours of different regions
        _, thresh = cv2.threshold(diff_image, diff_threshold, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:  # Ignore very small differences
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate difference severity based on area and intensity
            region_diff = np.mean(diff_image[y:y+h, x:x+w])
            
            if region_diff > 150:
                severity = "critical"
            elif region_diff > 100:
                severity = "major"
            else:
                severity = "minor"
            
            differences.append(VisualDifference(
                difference_type="structural",
                region={"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                severity=severity,
                description=f"Structural difference in region (SSIM: {region_diff/255:.3f})",
                confidence=min(1.0, region_diff / 255.0)
            ))
        
        return {
            "differences": differences,
            "similarity": float(similarity)
        }
    
    async def _pixel_level_comparison(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Perform pixel-level comparison"""
        differences = []
        
        # Calculate absolute difference
        diff = cv2.absdiff(img1, img2)
        
        # Convert to grayscale for analysis
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Calculate overall similarity
        total_pixels = gray_diff.size
        different_pixels = np.sum(gray_diff > self.pixel_threshold)
        similarity = 1.0 - (different_pixels / total_pixels)
        
        # Find regions with significant pixel differences
        _, thresh = cv2.threshold(gray_diff, self.pixel_threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Ignore very small differences
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate average difference intensity in region
            region_diff = np.mean(gray_diff[y:y+h, x:x+w])
            
            if region_diff > 150:
                severity = "critical"
            elif region_diff > 100:
                severity = "major"
            else:
                severity = "minor"
            
            differences.append(VisualDifference(
                difference_type="pixel",
                region={"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                severity=severity,
                description=f"Pixel-level difference (avg intensity: {region_diff:.1f})",
                confidence=min(1.0, region_diff / 255.0)
            ))
        
        return {
            "differences": differences,
            "similarity": float(similarity)
        }
    
    async def _color_comparison(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Compare color distributions and palettes"""
        differences = []
        
        # Convert to different color spaces for analysis
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
        
        # Compare histograms
        hist1_h = cv2.calcHist([hsv1], [0], None, [180], [0, 180])
        hist1_s = cv2.calcHist([hsv1], [1], None, [256], [0, 256])
        hist1_v = cv2.calcHist([hsv1], [2], None, [256], [0, 256])
        
        hist2_h = cv2.calcHist([hsv2], [0], None, [180], [0, 180])
        hist2_s = cv2.calcHist([hsv2], [1], None, [256], [0, 256])
        hist2_v = cv2.calcHist([hsv2], [2], None, [256], [0, 256])
        
        # Calculate histogram correlations
        corr_h = cv2.compareHist(hist1_h, hist2_h, cv2.HISTCMP_CORREL)
        corr_s = cv2.compareHist(hist1_s, hist2_s, cv2.HISTCMP_CORREL)
        corr_v = cv2.compareHist(hist1_v, hist2_v, cv2.HISTCMP_CORREL)
        
        # If there are significant color differences
        if corr_h < 0.9 or corr_s < 0.9 or corr_v < 0.9:
            differences.append(VisualDifference(
                difference_type="color_distribution",
                region={"x": 0, "y": 0, "width": img1.shape[1], "height": img1.shape[0]},
                severity="major" if min(corr_h, corr_s, corr_v) < 0.7 else "minor",
                description=f"Color distribution difference (H:{corr_h:.3f}, S:{corr_s:.3f}, V:{corr_v:.3f})",
                confidence=1.0 - min(corr_h, corr_s, corr_v)
            ))
        
        return {"differences": differences}
    
    async def _layout_comparison(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Compare layout and structural elements"""
        differences = []
        
        # Convert to grayscale and find edges
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        edges1 = cv2.Canny(gray1, 50, 150)
        edges2 = cv2.Canny(gray2, 50, 150)
        
        # Compare edge maps
        edge_diff = cv2.absdiff(edges1, edges2)
        
        # Find contours in edge differences
        contours, _ = cv2.findContours(edge_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 200:  # Ignore small edge differences
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            differences.append(VisualDifference(
                difference_type="layout",
                region={"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                severity="major",
                description="Layout/structural difference detected",
                confidence=min(1.0, area / 10000.0)
            ))
        
        return {"differences": differences}
    
    async def _text_region_comparison(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Compare text regions specifically"""
        differences = []
        
        # Use MSER to detect text regions
        mser = cv2.MSER_create()
        
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        regions1, _ = mser.detectRegions(gray1)
        regions2, _ = mser.detectRegions(gray2)
        
        # Simple comparison - count differences in number of text regions
        if abs(len(regions1) - len(regions2)) > 2:
            differences.append(VisualDifference(
                difference_type="text_regions",
                region={"x": 0, "y": 0, "width": img1.shape[1], "height": img1.shape[0]},
                severity="major",
                description=f"Different number of text regions: {len(regions1)} vs {len(regions2)}",
                confidence=min(1.0, abs(len(regions1) - len(regions2)) / 10.0)
            ))
        
        return {"differences": differences}
    
    def _filter_minor_differences(self, differences: List[VisualDifference]) -> List[VisualDifference]:
        """Filter out minor differences if configured"""
        if not self.ignore_minor:
            return differences
        
        return [diff for diff in differences if diff.severity != "minor" or diff.confidence > 0.7]
    
    def _get_comparison_methods(self, comparison_type: str) -> List[str]:
        """Get list of comparison methods used"""
        method_map = {
            "full": ["structural", "pixel", "color", "layout", "text"],
            "structural": ["structural"],
            "pixel": ["pixel"],
            "color": ["color"],
            "layout": ["layout"],
            "text": ["text"]
        }
        return method_map.get(comparison_type, ["structural", "pixel"])
    
    async def create_diff_visualization(
        self,
        result: VisualComparisonResult,
        output_path: str,
        highlight_differences: bool = True
    ) -> str:
        """Create a visual diff image highlighting differences"""
        try:
            # Load original images
            img1 = cv2.imread(result.image1_path)
            img2 = cv2.imread(result.image2_path)
            
            # Normalize images
            img1, img2 = self._normalize_images(img1, img2)
            
            if highlight_differences:
                # Create side-by-side comparison with highlighted differences
                height, width = img1.shape[:2]
                combined = np.zeros((height, width * 2, 3), dtype=np.uint8)
                
                # Place original images
                combined[:, :width] = img1
                combined[:, width:] = img2
                
                # Highlight differences on both sides
                for diff in result.differences:
                    if diff.severity == "critical":
                        color = (0, 0, 255)  # Red
                    elif diff.severity == "major":
                        color = (0, 165, 255)  # Orange
                    else:
                        color = (0, 255, 255)  # Yellow
                    
                    x, y, w, h = diff.region["x"], diff.region["y"], diff.region["width"], diff.region["height"]
                    
                    # Draw rectangle on both images
                    cv2.rectangle(combined, (x, y), (x + w, y + h), color, 2)
                    cv2.rectangle(combined, (x + width, y), (x + w + width, y + h), color, 2)
                
                # Add labels
                cv2.putText(combined, "Reference", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(combined, "Comparison", (width + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
            else:
                # Simple side-by-side without highlighting
                combined = np.hstack((img1, img2))
            
            # Save the diff image
            cv2.imwrite(output_path, combined)
            
            logger.info("Diff visualization created",
                       output_path=output_path,
                       differences_highlighted=len(result.differences))
            
            return output_path
            
        except Exception as e:
            logger.error("Failed to create diff visualization", error=str(e))
            raise