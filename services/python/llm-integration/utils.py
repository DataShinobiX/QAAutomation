"""
Utility functions for LLM Integration Service
"""
import asyncio
import time
import uuid
from typing import Dict, Any, Optional
import httpx
import structlog

logger = structlog.get_logger()


async def make_http_request(
    method: str,
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make HTTP request with proper error handling and timeout
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        json_data: JSON data for POST requests
        params: Query parameters
        headers: HTTP headers
        timeout: Request timeout in seconds
        
    Returns:
        Dict with success status and response data or error
    """
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Making HTTP request",
                       method=method,
                       url=url,
                       timeout=timeout)
            
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=headers or {}
            )
            
            processing_time = time.time() - start_time
            
            logger.info("HTTP request completed",
                       status_code=response.status_code,
                       processing_time=processing_time)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "success": True,
                        "data": data,
                        "status_code": response.status_code,
                        "processing_time": processing_time
                    }
                except Exception:
                    return {
                        "success": True,
                        "data": response.text,
                        "status_code": response.status_code,
                        "processing_time": processing_time
                    }
            else:
                logger.error("HTTP request failed",
                           status_code=response.status_code,
                           response_text=response.text[:200])
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code,
                    "processing_time": processing_time
                }
                
    except asyncio.TimeoutError:
        processing_time = time.time() - start_time
        logger.error("HTTP request timeout",
                    url=url,
                    timeout=timeout,
                    processing_time=processing_time)
        return {
            "success": False,
            "error": f"Request timeout after {timeout}s",
            "processing_time": processing_time
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error("HTTP request error",
                    url=url,
                    error=str(e),
                    processing_time=processing_time)
        return {
            "success": False,
            "error": str(e),
            "processing_time": processing_time
        }


def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def count_tokens_estimate(text: str) -> int:
    """Rough estimate of tokens in text (1 token ≈ 4 characters)"""
    return len(text) // 4


def is_valid_json(data: Any) -> bool:
    """Check if data can be serialized to JSON"""
    try:
        import json
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False