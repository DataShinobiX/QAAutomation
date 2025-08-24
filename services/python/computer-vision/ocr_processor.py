"""
OCR (Optical Character Recognition) Processor
Extracts text from images using multiple OCR engines
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import structlog
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class OCRResult:
    """OCR extraction result"""
    def __init__(
        self, 
        text: str, 
        confidence: float, 
        bounding_boxes: List[Dict[str, Any]] = None,
        language: str = "eng",
        engine: str = "tesseract"
    ):
        self.text = text
        self.confidence = confidence
        self.bounding_boxes = bounding_boxes or []
        self.language = language
        self.engine = engine
        self.extracted_at = datetime.utcnow()

class OCRProcessor:
    """Advanced OCR processor with multiple engines and preprocessing"""
    
    def __init__(self):
        # Initialize EasyOCR reader (supports many languages)
        self.easyocr_reader = None
        try:
            self.easyocr_reader = easyocr.Reader(['en', 'es', 'fr', 'de', 'it', 'pt'])
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.warning("EasyOCR initialization failed", error=str(e))
        
        # Configure Tesseract if available
        if config.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd
        
        logger.info("OCR Processor initialized", 
                   tesseract_available=self._check_tesseract_available(),
                   easyocr_available=bool(self.easyocr_reader))
    
    def _check_tesseract_available(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    async def extract_text_from_image(
        self, 
        image_path: str,
        language: str = "eng",
        preprocess: bool = True,
        engine: str = "auto"
    ) -> OCRResult:
        """
        Extract text from image using OCR
        
        Args:
            image_path: Path to image file
            language: Language for OCR (eng, spa, fra, etc.)
            preprocess: Whether to apply image preprocessing
            engine: OCR engine to use ('tesseract', 'easyocr', 'auto')
        """
        logger.info("Starting OCR text extraction", 
                   image_path=image_path, 
                   language=language, 
                   engine=engine)
        
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            if preprocess:
                image = self._preprocess_image(image)
            
            # Choose OCR engine
            if engine == "auto":
                # Try both engines and return best result
                results = []
                
                if self._check_tesseract_available():
                    tesseract_result = await self._extract_with_tesseract(image, language)
                    results.append(tesseract_result)
                
                if self.easyocr_reader:
                    easyocr_result = await self._extract_with_easyocr(image, language)
                    results.append(easyocr_result)
                
                # Return result with highest confidence
                if results:
                    best_result = max(results, key=lambda r: r.confidence)
                    logger.info("OCR extraction completed", 
                              engine=best_result.engine, 
                              confidence=best_result.confidence,
                              text_length=len(best_result.text))
                    return best_result
                else:
                    raise Exception("No OCR engines available")
            
            elif engine == "tesseract":
                if not self._check_tesseract_available():
                    raise Exception("Tesseract not available")
                return await self._extract_with_tesseract(image, language)
            
            elif engine == "easyocr":
                if not self.easyocr_reader:
                    raise Exception("EasyOCR not available")
                return await self._extract_with_easyocr(image, language)
            
            else:
                raise ValueError(f"Unknown OCR engine: {engine}")
                
        except Exception as e:
            logger.error("OCR text extraction failed", 
                        image_path=image_path, 
                        error=str(e))
            # Return empty result on failure
            return OCRResult("", 0.0, [], language, engine)
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply various preprocessing techniques
        
        # 1. Gaussian blur to reduce noise
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 2. Adaptive thresholding for better text contrast
        threshold = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 3. Morphological operations to clean up the image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        processed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
        
        # 4. Resize if image is too small (improves OCR accuracy)
        height, width = processed.shape
        if height < 100 or width < 100:
            scale_factor = max(100 / height, 100 / width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return processed
    
    async def _extract_with_tesseract(
        self, 
        image: np.ndarray, 
        language: str
    ) -> OCRResult:
        """Extract text using Tesseract OCR"""
        
        def _tesseract_ocr():
            # Convert language code if needed
            lang_map = {
                "eng": "eng", "spa": "spa", "fra": "fra", 
                "deu": "deu", "ita": "ita", "por": "por"
            }
            tesseract_lang = lang_map.get(language, "eng")
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?@#$%^&*()_+-=[]{}|;:,.<>?'
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(
                image, 
                lang=tesseract_lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Process results
            texts = []
            confidences = []
            bounding_boxes = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > config.ocr_confidence_threshold:
                    text = data['text'][i].strip()
                    if text:
                        texts.append(text)
                        confidences.append(int(conf))
                        
                        # Add bounding box info
                        bounding_boxes.append({
                            "x": int(data['left'][i]),
                            "y": int(data['top'][i]),
                            "width": int(data['width'][i]),
                            "height": int(data['height'][i]),
                            "text": text,
                            "confidence": int(conf)
                        })
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                language=language,
                engine="tesseract"
            )
        
        # Run Tesseract in thread to avoid blocking
        return await asyncio.to_thread(_tesseract_ocr)
    
    async def _extract_with_easyocr(
        self, 
        image: np.ndarray, 
        language: str
    ) -> OCRResult:
        """Extract text using EasyOCR"""
        
        def _easyocr_ocr():
            # EasyOCR expects RGB, OpenCV uses BGR
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extract text
            results = self.easyocr_reader.readtext(rgb_image)
            
            texts = []
            bounding_boxes = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > (config.ocr_confidence_threshold / 100.0):  # EasyOCR uses 0-1 scale
                    texts.append(text)
                    confidences.append(confidence * 100)  # Convert to 0-100 scale
                    
                    # Convert bounding box format
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    bounding_boxes.append({
                        "x": int(min(x_coords)),
                        "y": int(min(y_coords)),
                        "width": int(max(x_coords) - min(x_coords)),
                        "height": int(max(y_coords) - min(y_coords)),
                        "text": text,
                        "confidence": confidence * 100
                    })
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                language=language,
                engine="easyocr"
            )
        
        # Run EasyOCR in thread to avoid blocking
        return await asyncio.to_thread(_easyocr_ocr)
    
    async def extract_text_from_region(
        self,
        image_path: str,
        region: Dict[str, int],
        language: str = "eng",
        engine: str = "auto"
    ) -> OCRResult:
        """
        Extract text from a specific region of an image
        
        Args:
            image_path: Path to image file
            region: Dictionary with x, y, width, height keys
            language: Language for OCR
            engine: OCR engine to use
        """
        logger.info("Extracting text from image region", 
                   image_path=image_path, 
                   region=region)
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Extract region
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Ensure region is within image bounds
            img_height, img_width = image.shape[:2]
            x = max(0, min(x, img_width))
            y = max(0, min(y, img_height))
            w = min(w, img_width - x)
            h = min(h, img_height - y)
            
            region_image = image[y:y+h, x:x+w]
            
            # Save region to temporary file
            temp_path = f"/tmp/ocr_region_{datetime.utcnow().timestamp()}.png"
            cv2.imwrite(temp_path, region_image)
            
            try:
                # Extract text from region
                result = await self.extract_text_from_image(temp_path, language, True, engine)
                
                # Adjust bounding box coordinates to original image space
                for bbox in result.bounding_boxes:
                    bbox['x'] += x
                    bbox['y'] += y
                
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error("Region OCR extraction failed", 
                        image_path=image_path,
                        region=region,
                        error=str(e))
            return OCRResult("", 0.0, [], language, engine)
    
    async def batch_extract_text(
        self,
        image_paths: List[str],
        language: str = "eng",
        engine: str = "auto",
        max_concurrent: int = 3
    ) -> List[OCRResult]:
        """
        Extract text from multiple images concurrently
        """
        logger.info("Starting batch OCR extraction", 
                   image_count=len(image_paths), 
                   max_concurrent=max_concurrent)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single(image_path: str) -> OCRResult:
            async with semaphore:
                return await self.extract_text_from_image(image_path, language, True, engine)
        
        results = await asyncio.gather(
            *[extract_single(path) for path in image_paths],
            return_exceptions=True
        )
        
        # Filter out exceptions and convert to OCRResult
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Batch OCR failed for image", 
                           image_path=image_paths[i], 
                           error=str(result))
                valid_results.append(OCRResult("", 0.0, [], language, engine))
            else:
                valid_results.append(result)
        
        logger.info("Batch OCR extraction completed", 
                   processed=len(valid_results),
                   successful=sum(1 for r in valid_results if r.confidence > 0))
        
        return valid_results