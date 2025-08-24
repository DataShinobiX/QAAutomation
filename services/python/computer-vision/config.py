"""
Computer Vision Service Configuration
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class ComputerVisionConfig(BaseSettings):
    """Computer Vision Service Configuration"""
    
    # Service Configuration
    service_name: str = "computer-vision"
    version: str = "1.0.0"
    port: int = int(os.getenv("PORT", 8004))
    host: str = "0.0.0.0"
    
    # OCR Configuration
    tesseract_cmd: Optional[str] = os.getenv("TESSERACT_CMD")  # Path to tesseract executable
    ocr_languages: List[str] = ["eng", "spa", "fra", "deu", "ita", "por"]  # Supported languages
    ocr_confidence_threshold: float = 60.0  # Minimum confidence for OCR results
    
    # Computer Vision Configuration
    cv_resize_max_width: int = 1920  # Max width for processing
    cv_resize_max_height: int = 1080  # Max height for processing
    component_detection_confidence: float = 0.5  # Confidence threshold for component detection
    
    # Accessibility Configuration
    min_contrast_ratio_aa: float = 4.5  # WCAG AA minimum contrast ratio
    min_contrast_ratio_aaa: float = 7.0  # WCAG AAA minimum contrast ratio
    min_text_size_pt: float = 12.0  # Minimum text size in points
    
    # Visual Comparison Configuration  
    visual_similarity_threshold: float = 0.95  # Threshold for considering images similar
    pixel_difference_threshold: int = 50  # RGB difference threshold for pixel comparison
    ignore_minor_changes: bool = True  # Ignore minor visual changes
    
    # File Processing Configuration
    max_file_size_mb: int = 50  # Maximum file size for processing
    supported_image_formats: List[str] = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]
    temp_directory: str = "/tmp/cv_processing"
    
    # Service Integration URLs
    visual_engine_url: str = "http://localhost:3002"
    test_executor_url: str = "http://localhost:3003"
    orchestrator_url: str = "http://localhost:8006"
    
    # Database Configuration
    redis_url: str = "redis://localhost:6379/4"  # Use database 4 for computer vision
    postgres_url: str = "postgresql://user:password@localhost:5432/qa_automation"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global configuration instance
config = ComputerVisionConfig()