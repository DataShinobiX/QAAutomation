"""
Figma API Client
Handles all interactions with the Figma REST API
"""
import asyncio
import httpx
import structlog
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from config import FigmaServiceConfig

logger = structlog.get_logger()


class FigmaAPIError(Exception):
    """Custom exception for Figma API errors"""
    pass


class FigmaClient:
    """Client for Figma REST API"""
    
    def __init__(self, config: FigmaServiceConfig):
        self.config = config
        self.base_url = config.figma_api_base_url
        self.token = config.figma_token
        self.headers = {
            "X-Figma-Token": self.token,
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test connection to Figma API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error("Figma API connection test failed", error=str(e))
            raise FigmaAPIError(f"Failed to connect to Figma API: {str(e)}")
    
    async def get_file(self, file_key: str) -> Dict[str, Any]:
        """Get a Figma file"""
        url = f"{self.base_url}/files/{file_key}"
        
        logger.info("Fetching Figma file", file_key=file_key, url=url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info("Successfully fetched Figma file", 
                           file_key=file_key, 
                           document_name=data.get("name", "Unknown"))
                
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching Figma file", 
                        file_key=file_key, 
                        status_code=e.response.status_code,
                        response_text=e.response.text)
            raise FigmaAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
            
        except Exception as e:
            logger.error("Unexpected error fetching Figma file", 
                        file_key=file_key, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch file: {str(e)}")
    
    async def get_file_nodes(self, file_key: str, node_ids: List[str]) -> Dict[str, Any]:
        """Get specific nodes from a Figma file"""
        if not node_ids:
            raise FigmaAPIError("Node IDs are required")
        
        url = f"{self.base_url}/files/{file_key}/nodes"
        params = {"ids": ",".join(node_ids)}
        
        logger.info("Fetching Figma file nodes", 
                   file_key=file_key, 
                   node_count=len(node_ids))
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching Figma nodes", 
                        file_key=file_key,
                        status_code=e.response.status_code)
            raise FigmaAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
            
        except Exception as e:
            logger.error("Error fetching Figma nodes", 
                        file_key=file_key, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch nodes: {str(e)}")
    
    async def get_images(
        self, 
        file_key: str, 
        node_ids: List[str],
        scale: float = 1.0,
        format: str = "png"
    ) -> Dict[str, Any]:
        """Get images/renders of Figma nodes"""
        if not node_ids:
            # If no specific nodes, get first few frames (limit to avoid URL length issues)
            file_data = await self.get_file(file_key)
            all_frame_ids = self._extract_frame_ids(file_data)
            node_ids = all_frame_ids[:10]  # Limit to first 10 frames
        
        url = f"{self.base_url}/images/{file_key}"
        params = {
            "ids": ",".join(node_ids),
            "scale": scale,
            "format": format
        }
        
        logger.info("Fetching Figma images", 
                   file_key=file_key, 
                   node_count=len(node_ids),
                   scale=scale,
                   format=format)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=60.0  # Image generation can take longer
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info("Successfully fetched Figma images", 
                           file_key=file_key,
                           image_count=len(result.get("images", {})))
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching Figma images", 
                        file_key=file_key,
                        status_code=e.response.status_code)
            raise FigmaAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
            
        except Exception as e:
            logger.error("Error fetching Figma images", 
                        file_key=file_key, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch images: {str(e)}")
    
    async def get_file_versions(self, file_key: str) -> Dict[str, Any]:
        """Get version history of a Figma file"""
        url = f"{self.base_url}/files/{file_key}/versions"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error("Error fetching file versions", 
                        file_key=file_key, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch versions: {str(e)}")
    
    async def get_team_styles(self, team_id: str) -> Dict[str, Any]:
        """Get team styles (colors, text styles, etc.)"""
        url = f"{self.base_url}/teams/{team_id}/styles"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error("Error fetching team styles", 
                        team_id=team_id, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch team styles: {str(e)}")
    
    def _extract_frame_ids(self, file_data: Dict[str, Any]) -> List[str]:
        """Extract frame IDs from file data"""
        frame_ids = []
        
        def traverse_nodes(node):
            if node.get("type") == "FRAME":
                frame_ids.append(node["id"])
            
            for child in node.get("children", []):
                traverse_nodes(child)
        
        # Traverse all pages
        document = file_data.get("document", {})
        for page in document.get("children", []):
            traverse_nodes(page)
        
        return frame_ids
    
    async def download_image(self, image_url: str) -> bytes:
        """Download an image from Figma CDN"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30.0)
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            logger.error("Error downloading image", url=image_url, error=str(e))
            raise FigmaAPIError(f"Failed to download image: {str(e)}")
    
    async def get_file_components(self, file_key: str) -> Dict[str, Any]:
        """Get all components in a file"""
        url = f"{self.base_url}/files/{file_key}/components"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error("Error fetching file components", 
                        file_key=file_key, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch components: {str(e)}")
    
    async def get_component_sets(self, file_key: str) -> Dict[str, Any]:
        """Get component sets (variants) in a file"""
        url = f"{self.base_url}/files/{file_key}/component_sets"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error("Error fetching component sets", 
                        file_key=file_key, 
                        error=str(e))
            raise FigmaAPIError(f"Failed to fetch component sets: {str(e)}")