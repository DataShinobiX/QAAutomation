"""
Rate Limiter for LLM API calls
Manages rate limiting to prevent API quota exhaustion
"""
import asyncio
import time
from typing import Dict, Any
import structlog
import aioredis
from datetime import datetime, timedelta

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter for LLM API calls"""
    
    def __init__(self, config):
        self.config = config
        self.redis_client = None
        self._local_cache = {}
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for distributed rate limiting"""
        try:
            # Try to connect to Redis for distributed rate limiting
            redis_url = self.config.redis_url
            if redis_url:
                # This will be set up asynchronously
                self._redis_url = redis_url
            else:
                logger.warning("Redis URL not provided, using local rate limiting only")
        except Exception as e:
            logger.warning("Redis connection failed, using local rate limiting", error=str(e))
    
    async def _get_redis_client(self):
        """Get Redis client with lazy initialization"""
        if self.redis_client is None and hasattr(self, '_redis_url'):
            try:
                self.redis_client = await aioredis.from_url(self._redis_url)
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.warning("Failed to connect to Redis, using local cache", error=str(e))
        
        return self.redis_client
    
    async def check_rate_limit(self, operation: str, provider: str) -> bool:
        """Check if operation is within rate limits"""
        key = f"rate_limit:{provider}:{operation}"
        current_time = time.time()
        
        # Try Redis first, fallback to local cache
        redis_client = await self._get_redis_client()
        
        if redis_client:
            return await self._check_redis_rate_limit(redis_client, key, current_time)
        else:
            return await self._check_local_rate_limit(key, current_time)
    
    async def _check_redis_rate_limit(self, redis_client, key: str, current_time: float) -> bool:
        """Check rate limit using Redis"""
        try:
            # Get current request count for this minute
            minute_key = f"{key}:minute:{int(current_time // 60)}"
            hour_key = f"{key}:hour:{int(current_time // 3600)}"
            
            # Check per-minute limit
            minute_count = await redis_client.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0
            
            # Check per-hour limit
            hour_count = await redis_client.get(hour_key)
            hour_count = int(hour_count) if hour_count else 0
            
            # Get limits for provider
            minute_limit, hour_limit = self._get_provider_limits()
            
            if minute_count >= minute_limit or hour_count >= hour_limit:
                logger.warning("Rate limit exceeded",
                             minute_count=minute_count,
                             hour_count=hour_count,
                             minute_limit=minute_limit,
                             hour_limit=hour_limit)
                return False
            
            # Increment counters
            await redis_client.incr(minute_key)
            await redis_client.expire(minute_key, 60)
            
            await redis_client.incr(hour_key)
            await redis_client.expire(hour_key, 3600)
            
            logger.debug("Rate limit check passed",
                        minute_count=minute_count + 1,
                        hour_count=hour_count + 1)
            
            return True
            
        except Exception as e:
            logger.error("Redis rate limit check failed", error=str(e))
            # Fallback to local rate limiting
            return await self._check_local_rate_limit(key, current_time)
    
    async def _check_local_rate_limit(self, key: str, current_time: float) -> bool:
        """Check rate limit using local cache"""
        minute_key = f"{key}:minute:{int(current_time // 60)}"
        hour_key = f"{key}:hour:{int(current_time // 3600)}"
        
        # Clean old entries
        self._cleanup_local_cache(current_time)
        
        # Check current counts
        minute_count = self._local_cache.get(minute_key, 0)
        hour_count = self._local_cache.get(hour_key, 0)
        
        # Get limits
        minute_limit, hour_limit = self._get_provider_limits()
        
        if minute_count >= minute_limit or hour_count >= hour_limit:
            logger.warning("Local rate limit exceeded",
                         minute_count=minute_count,
                         hour_count=hour_count)
            return False
        
        # Increment counters
        self._local_cache[minute_key] = minute_count + 1
        self._local_cache[hour_key] = hour_count + 1
        
        return True
    
    def _get_provider_limits(self) -> tuple[int, int]:
        """Get rate limits for provider (per minute, per hour)"""
        # Azure OpenAI limits (conservative defaults)
        return (
            self.config.requests_per_minute,  # requests per minute
            self.config.requests_per_hour     # requests per hour
        )
    
    def _cleanup_local_cache(self, current_time: float):
        """Clean up old entries from local cache"""
        current_minute = int(current_time // 60)
        current_hour = int(current_time // 3600)
        
        # Remove entries older than 2 hours
        keys_to_remove = []
        for key in self._local_cache:
            if ":minute:" in key:
                minute = int(key.split(":minute:")[1])
                if minute < current_minute - 2:  # Keep last 2 minutes
                    keys_to_remove.append(key)
            elif ":hour:" in key:
                hour = int(key.split(":hour:")[1])
                if hour < current_hour - 2:  # Keep last 2 hours
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._local_cache[key]
    
    async def get_rate_limit_status(self, provider: str) -> Dict[str, Any]:
        """Get current rate limit status"""
        current_time = time.time()
        minute_key = f"rate_limit:{provider}:generate:minute:{int(current_time // 60)}"
        hour_key = f"rate_limit:{provider}:generate:hour:{int(current_time // 3600)}"
        
        redis_client = await self._get_redis_client()
        
        minute_limit, hour_limit = self._get_provider_limits()
        
        if redis_client:
            try:
                minute_count = await redis_client.get(minute_key)
                hour_count = await redis_client.get(hour_key)
                minute_count = int(minute_count) if minute_count else 0
                hour_count = int(hour_count) if hour_count else 0
            except Exception:
                minute_count = self._local_cache.get(minute_key, 0)
                hour_count = self._local_cache.get(hour_key, 0)
        else:
            minute_count = self._local_cache.get(minute_key, 0)
            hour_count = self._local_cache.get(hour_key, 0)
        
        return {
            "provider": provider,
            "current_minute": {
                "count": minute_count,
                "limit": minute_limit,
                "remaining": max(0, minute_limit - minute_count)
            },
            "current_hour": {
                "count": hour_count,
                "limit": hour_limit,
                "remaining": max(0, hour_limit - hour_count)
            },
            "reset_times": {
                "next_minute": datetime.fromtimestamp((int(current_time // 60) + 1) * 60),
                "next_hour": datetime.fromtimestamp((int(current_time // 3600) + 1) * 3600)
            }
        }
    
    async def wait_for_rate_limit(self, operation: str, provider: str, max_wait: int = 60):
        """Wait until rate limit allows the operation"""
        wait_time = 1
        max_wait_time = max_wait
        
        while wait_time <= max_wait_time:
            if await self.check_rate_limit(operation, provider):
                return True
            
            logger.info("Rate limit hit, waiting",
                       wait_time=wait_time,
                       operation=operation,
                       provider=provider)
            
            await asyncio.sleep(wait_time)
            wait_time = min(wait_time * 2, max_wait_time)  # Exponential backoff
        
        logger.error("Rate limit wait timeout exceeded",
                    max_wait=max_wait,
                    operation=operation,
                    provider=provider)
        return False
    
    async def reset_rate_limits(self, provider: str = None):
        """Reset rate limits (for testing/admin purposes)"""
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                pattern = f"rate_limit:{provider or '*'}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                logger.info("Reset Redis rate limits", provider=provider, keys_deleted=len(keys))
            except Exception as e:
                logger.error("Failed to reset Redis rate limits", error=str(e))
        
        # Also clear local cache
        if provider:
            keys_to_remove = [k for k in self._local_cache.keys() if f":{provider}:" in k]
        else:
            keys_to_remove = list(self._local_cache.keys())
        
        for key in keys_to_remove:
            del self._local_cache[key]
        
        logger.info("Reset local rate limits", provider=provider, keys_deleted=len(keys_to_remove))
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")