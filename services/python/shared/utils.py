"""
Shared utility functions for Python AI services
"""
import asyncio
import httpx
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json


logger = structlog.get_logger()


async def make_http_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """Make an HTTP request with proper error handling"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data
            )
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json() if response.content else {},
                "status_code": response.status_code
            }
        except httpx.HTTPStatusError as e:
            logger.error("HTTP request failed", url=url, status_code=e.response.status_code)
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "status_code": e.response.status_code
            }
        except httpx.RequestError as e:
            logger.error("Request error", url=url, error=str(e))
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "status_code": 0
            }


async def call_rust_service(
    service_url: str,
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Call a Rust service (website-analyzer, visual-engine, test-executor)"""
    url = f"{service_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    logger.info("Calling Rust service", service_url=service_url, endpoint=endpoint)
    
    return await make_http_request(
        method=method,
        url=url,
        json_data=data
    )


def generate_id() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def format_timestamp(dt: datetime = None) -> str:
    """Format datetime for consistent logging"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat() + "Z"


def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON with error handling"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse JSON", error=str(e), text=text[:100])
        return None


def extract_selectors_from_text(text: str) -> list:
    """Extract CSS selectors or XPath from text"""
    # This is a basic implementation - can be enhanced with regex
    selectors = []
    
    # Look for common CSS selectors
    import re
    css_pattern = r'[#\.][\w-]+|[\w-]+\[[\w-]+=?"?[\w-]+"?\]'
    css_matches = re.findall(css_pattern, text)
    selectors.extend(css_matches)
    
    # Look for XPath expressions
    xpath_pattern = r'//[\w\[\]@="\':\s/-]+'
    xpath_matches = re.findall(xpath_pattern, text)
    selectors.extend(xpath_matches)
    
    return list(set(selectors))  # Remove duplicates


def color_hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (0, 0, 0)


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex color"""
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def calculate_color_difference(color1: str, color2: str) -> float:
    """Calculate color difference between two hex colors (0-1 scale)"""
    rgb1 = color_hex_to_rgb(color1)
    rgb2 = color_hex_to_rgb(color2)
    
    # Calculate Euclidean distance
    diff = sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5
    # Normalize to 0-1 scale (max difference is sqrt(3*255^2))
    return min(diff / (255 * 1.732), 1.0)


async def retry_with_backoff(
    func, 
    max_retries: int = 3, 
    base_delay: float = 1.0,
    *args, 
    **kwargs
):
    """Retry a function with exponential backoff"""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                break
            
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Function failed, retrying",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(e)
            )
            await asyncio.sleep(delay)
    
    raise last_exception


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    return urlparse(url).netloc