"""
Figma Design Analyzer
Analyzes Figma designs and extracts UI components, layouts, styles
"""
import asyncio
import structlog
from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass

from config import FigmaServiceConfig
from figma_client import FigmaClient
from models import FigmaComponent, FigmaFrame, FigmaDesign
from utils import color_hex_to_rgb, rgb_to_hex, make_http_request

logger = structlog.get_logger()


@dataclass
class ColorInfo:
    """Color information with usage context"""
    hex: str
    rgb: Tuple[int, int, int]
    usage: str  # background, text, border, etc.
    count: int = 1


@dataclass
class Typography:
    """Typography information"""
    font_family: str
    font_size: float
    font_weight: str
    line_height: Optional[float] = None
    letter_spacing: Optional[float] = None
    usage: str = "body"  # heading, body, caption, etc.


class FigmaAnalyzer:
    """Analyzes Figma files to extract design information"""
    
    def __init__(self, config: FigmaServiceConfig):
        self.config = config
        self.figma_client = FigmaClient(config)
    
    async def analyze_file(self, file_data: Dict[str, Any]) -> FigmaDesign:
        """Analyze complete Figma file"""
        logger.info("Starting Figma file analysis", 
                   file_name=file_data.get("name", "Unknown"))
        
        design = FigmaDesign(
            file_key=self.config.figma_file_key,
            name=file_data.get("name", "Unknown"),
            version=file_data.get("version", "1.0")
        )
        
        # Extract frames from all pages
        document = file_data.get("document", {})
        for page in document.get("children", []):
            if page.get("type") == "CANVAS":
                frames = await self._extract_frames_from_page(page)
                design.frames.extend(frames)
        
        # Extract global styles
        design.styles = await self._extract_global_styles(file_data)
        
        logger.info("Completed Figma file analysis", 
                   frames_count=len(design.frames),
                   styles_count=len(design.styles))
        
        return design
    
    async def _extract_frames_from_page(self, page: Dict[str, Any]) -> List[FigmaFrame]:
        """Extract all frames from a page"""
        frames = []
        
        for child in page.get("children", []):
            if child.get("type") == "FRAME":
                frame = await self._analyze_frame(child)
                frames.append(frame)
        
        return frames
    
    async def _analyze_frame(self, frame_data: Dict[str, Any]) -> FigmaFrame:
        """Analyze a single frame"""
        frame = FigmaFrame(
            id=frame_data["id"],
            name=frame_data["name"],
            width=frame_data["absoluteBoundingBox"]["width"],
            height=frame_data["absoluteBoundingBox"]["height"]
        )
        
        # Extract background color
        if "backgroundColor" in frame_data:
            bg_color = frame_data["backgroundColor"]
            frame.background_color = self._rgba_to_hex(bg_color)
        
        # Recursively analyze all components in frame
        frame.components = await self._extract_components(frame_data)
        
        logger.info("Analyzed frame", 
                   frame_name=frame.name,
                   components_count=len(frame.components))
        
        return frame
    
    async def _extract_components(self, node: Dict[str, Any]) -> List[FigmaComponent]:
        """Recursively extract components from a node"""
        components = []
        
        # Process current node
        component = await self._analyze_component(node)
        components.append(component)
        
        # Process children
        for child in node.get("children", []):
            child_components = await self._extract_components(child)
            component.children.extend(child_components)
        
        return components
    
    async def _analyze_component(self, node: Dict[str, Any]) -> FigmaComponent:
        """Analyze a single component/node"""
        bbox = node.get("absoluteBoundingBox", {})
        
        component = FigmaComponent(
            id=node["id"],
            name=node["name"],
            type=node["type"],
            x=bbox.get("x", 0),
            y=bbox.get("y", 0),
            width=bbox.get("width", 0),
            height=bbox.get("height", 0)
        )
        
        # Extract fills (colors, gradients, images)
        component.fills = node.get("fills", [])
        
        # Extract strokes (borders)
        component.strokes = node.get("strokes", [])
        
        # Extract effects (shadows, blurs)
        component.effects = node.get("effects", [])
        
        # Extract text content
        if node["type"] == "TEXT":
            component.characters = node.get("characters", "")
            component.style = await self._extract_text_style(node)
        
        # Extract button-specific properties
        if self._is_button_component(node):
            component.style["component_type"] = "button"
            component.style["interactive"] = True
        
        # Extract input-specific properties
        elif self._is_input_component(node):
            component.style["component_type"] = "input"
            component.style["interactive"] = True
        
        return component
    
    def _is_button_component(self, node: Dict[str, Any]) -> bool:
        """Detect if component is likely a button"""
        name = node["name"].lower()
        return any(keyword in name for keyword in [
            "button", "btn", "cta", "submit", "action"
        ])
    
    def _is_input_component(self, node: Dict[str, Any]) -> bool:
        """Detect if component is likely an input field"""
        name = node["name"].lower()
        return any(keyword in name for keyword in [
            "input", "field", "textbox", "search", "form"
        ])
    
    async def _extract_text_style(self, text_node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text styling information"""
        style = {}
        
        # Font properties
        if "style" in text_node:
            text_style = text_node["style"]
            style.update({
                "font_family": text_style.get("fontFamily", ""),
                "font_size": text_style.get("fontSize", 16),
                "font_weight": text_style.get("fontWeight", 400),
                "line_height": text_style.get("lineHeightPx"),
                "letter_spacing": text_style.get("letterSpacing"),
                "text_align": text_style.get("textAlignHorizontal", "left").lower()
            })
        
        return style
    
    async def _extract_global_styles(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract global styles (colors, typography, spacing)"""
        styles = {
            "colors": await self._extract_color_palette(file_data),
            "typography": await self._extract_typography_styles(file_data),
            "spacing": await self._extract_spacing_patterns(file_data)
        }
        
        return styles
    
    async def _extract_color_palette(self, file_data: Dict[str, Any]) -> Dict[str, ColorInfo]:
        """Extract color palette from the design"""
        colors = {}
        
        def collect_colors(node):
            # Collect from fills
            for fill in node.get("fills", []):
                if fill.get("type") == "SOLID":
                    color = fill.get("color", {})
                    hex_color = self._rgba_to_hex(color)
                    if hex_color:
                        if hex_color in colors:
                            colors[hex_color].count += 1
                        else:
                            colors[hex_color] = ColorInfo(
                                hex=hex_color,
                                rgb=color_hex_to_rgb(hex_color),
                                usage="fill"
                            )
            
            # Collect from strokes
            for stroke in node.get("strokes", []):
                if stroke.get("type") == "SOLID":
                    color = stroke.get("color", {})
                    hex_color = self._rgba_to_hex(color)
                    if hex_color:
                        if hex_color in colors:
                            colors[hex_color].count += 1
                        else:
                            colors[hex_color] = ColorInfo(
                                hex=hex_color,
                                rgb=color_hex_to_rgb(hex_color),
                                usage="stroke"
                            )
            
            # Recursively collect from children
            for child in node.get("children", []):
                collect_colors(child)
        
        # Start from document root
        collect_colors(file_data.get("document", {}))
        
        # Convert to serializable format
        return {hex_color: {
            "hex": info.hex,
            "rgb": info.rgb,
            "usage": info.usage,
            "count": info.count
        } for hex_color, info in colors.items()}
    
    async def _extract_typography_styles(self, file_data: Dict[str, Any]) -> Dict[str, Typography]:
        """Extract typography styles"""
        typography = {}
        
        def collect_text_styles(node):
            if node.get("type") == "TEXT" and "style" in node:
                style = node["style"]
                font_key = f"{style.get('fontFamily', 'default')}_{style.get('fontSize', 16)}"
                
                if font_key not in typography:
                    typography[font_key] = Typography(
                        font_family=style.get("fontFamily", ""),
                        font_size=style.get("fontSize", 16),
                        font_weight=str(style.get("fontWeight", 400)),
                        line_height=style.get("lineHeightPx"),
                        letter_spacing=style.get("letterSpacing"),
                        usage=self._determine_text_usage(node["name"])
                    )
            
            for child in node.get("children", []):
                collect_text_styles(child)
        
        collect_text_styles(file_data.get("document", {}))
        
        # Convert to serializable format
        return {key: {
            "font_family": typ.font_family,
            "font_size": typ.font_size,
            "font_weight": typ.font_weight,
            "line_height": typ.line_height,
            "letter_spacing": typ.letter_spacing,
            "usage": typ.usage
        } for key, typ in typography.items()}
    
    def _determine_text_usage(self, name: str) -> str:
        """Determine text usage from component name"""
        name_lower = name.lower()
        if any(word in name_lower for word in ["title", "heading", "header", "h1", "h2", "h3"]):
            return "heading"
        elif any(word in name_lower for word in ["caption", "small", "note"]):
            return "caption"
        else:
            return "body"
    
    async def _extract_spacing_patterns(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract common spacing patterns"""
        spacings = {
            "margins": [],
            "paddings": [],
            "gaps": []
        }
        
        def collect_spacing(node, parent_node=None):
            # Collect spacing between siblings
            if parent_node:
                bbox = node.get("absoluteBoundingBox", {})
                parent_bbox = parent_node.get("absoluteBoundingBox", {})
                
                if bbox and parent_bbox:
                    # Calculate relative positioning
                    margin_x = bbox.get("x", 0) - parent_bbox.get("x", 0)
                    margin_y = bbox.get("y", 0) - parent_bbox.get("y", 0)
                    
                    if margin_x > 0:
                        spacings["margins"].append(margin_x)
                    if margin_y > 0:
                        spacings["margins"].append(margin_y)
            
            # Recursively process children
            for child in node.get("children", []):
                collect_spacing(child, node)
        
        collect_spacing(file_data.get("document", {}))
        
        # Find common spacing values
        common_spacings = {}
        for space_type, values in spacings.items():
            if values:
                # Find most common values (simplified)
                unique_values = list(set(values))
                common_spacings[space_type] = sorted(unique_values)[:10]  # Top 10
        
        return common_spacings
    
    def _rgba_to_hex(self, color: Dict[str, float]) -> Optional[str]:
        """Convert RGBA color to hex"""
        try:
            r = int(color.get("r", 0) * 255)
            g = int(color.get("g", 0) * 255)
            b = int(color.get("b", 0) * 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (KeyError, ValueError):
            return None
    
    async def compare_with_website(
        self, 
        file_key: str, 
        target_url: str, 
        frame_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare Figma design with live website"""
        logger.info("Starting Figma-to-website comparison", 
                   file_key=file_key, target_url=target_url)
        
        # Get Figma file data
        file_data = await self.figma_client.get_file(file_key)
        design = await self.analyze_file(file_data)
        
        # Find target frame
        target_frame = None
        if frame_name:
            target_frame = next((f for f in design.frames if f.name == frame_name), None)
        else:
            target_frame = design.frames[0] if design.frames else None
        
        if not target_frame:
            raise ValueError(f"Frame '{frame_name}' not found")
        
        # Call website analyzer service
        website_data = await make_http_request(
            "POST",
            f"{self.config.website_analyzer_url}/analyze",
            json_data={"url": target_url}
        )
        
        if not website_data["success"]:
            raise Exception(f"Failed to analyze website: {website_data.get('error')}")
        
        # Compare design vs implementation
        comparison = await self._perform_comparison(target_frame, website_data["data"])
        
        logger.info("Completed Figma-to-website comparison", 
                   issues_found=len(comparison.get("issues", [])))
        
        return comparison
    
    async def _perform_comparison(
        self, 
        figma_frame: FigmaFrame, 
        website_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform detailed comparison between Figma and website"""
        issues = []
        matches = []
        
        # Compare colors
        figma_colors = set()
        for component in figma_frame.components:
            for fill in component.fills:
                if fill.get("type") == "SOLID":
                    color = self._rgba_to_hex(fill.get("color", {}))
                    if color:
                        figma_colors.add(color.upper())
        
        # Extract colors from website (this would need enhancement)
        website_colors = set()  # TODO: Extract from website analysis
        
        color_diff = figma_colors - website_colors
        if color_diff:
            issues.append({
                "type": "color_mismatch",
                "message": f"Colors missing in implementation: {list(color_diff)}"
            })
        
        # Compare layout structure (simplified)
        figma_components = len(figma_frame.components)
        website_elements = len(website_data.get("analysis", {}).get("dom_structure", {}).get("children", []))
        
        if abs(figma_components - website_elements) > 5:  # Threshold
            issues.append({
                "type": "structure_mismatch", 
                "message": f"Component count difference: Figma {figma_components}, Website {website_elements}"
            })
        
        return {
            "figma_frame": figma_frame.name,
            "website_url": website_data.get("analysis", {}).get("url"),
            "issues": issues,
            "matches": matches,
            "score": max(0, 100 - len(issues) * 10)  # Simple scoring
        }
    
    async def extract_styles(self, file_key: str) -> Dict[str, Any]:
        """Extract complete style guide from Figma file"""
        file_data = await self.figma_client.get_file(file_key)
        styles = await self._extract_global_styles(file_data)
        
        return {
            "file_key": file_key,
            "styles": styles,
            "style_guide": {
                "primary_colors": self._identify_primary_colors(styles["colors"]),
                "heading_styles": self._identify_heading_styles(styles["typography"]),
                "common_spacings": styles["spacing"]
            }
        }
    
    def _identify_primary_colors(self, colors: Dict[str, Any]) -> List[str]:
        """Identify primary brand colors"""
        # Sort by usage count and return top colors
        sorted_colors = sorted(
            colors.items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        )
        return [color[0] for color in sorted_colors[:5]]
    
    def _identify_heading_styles(self, typography: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify heading typography styles"""
        headings = []
        for key, style in typography.items():
            if style["usage"] == "heading":
                headings.append(style)
        
        # Sort by font size (largest first)
        return sorted(headings, key=lambda x: x["font_size"], reverse=True)