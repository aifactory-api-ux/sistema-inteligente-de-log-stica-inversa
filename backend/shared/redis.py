# backend/shared/redis.py

import json
import logging
from typing import Optional, Any
from datetime import timedelta
import redis.asyncio as redis

from config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
        return None


async def cache_set(
    key: str,
    value: Any,
    expire_seconds: int = 300,
) -> bool:
    """Set value in cache with expiration"""
    try:
        client = await get_redis()
        serialized = json.dumps(value, default=str)
        await client.setex(key, expire_seconds, serialized)
        return True
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error for key {key}: {e}")
        return False


async def cache_clear_pattern(pattern: str) -> int:
    """Delete all keys matching pattern"""
    try:
        client = await get_redis()
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache clear pattern error for {pattern}: {e}")
        return 0


async def rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """
    Rate limiting using sliding window counter.
    Returns (allowed, remaining_requests)
    """
    try:
        client = await get_redis()
        now = await client.time()
        current_time = now[0]

        window_key = f"ratelimit:{key}:{current_time // window_seconds}"

        pipe = client.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window_seconds * 2)
        results = await pipe.execute()

        current_count = results[0]
        remaining = max(0, max_requests - current_count)
        allowed = current_count <= max_requests

        return allowed, remaining
    except Exception as e:
        logger.warning(f"Rate limit error for {key}: {e}")
        return True, max_requests


async def acquire_lock(
    lock_name: str,
    timeout_seconds: int = 30,
    retry_times: int = 3,
    retry_delay_seconds: float = 0.1,
) -> bool:
    """Acquire a distributed lock"""
    try:
        client = await get_redis()
        lock_key = f"lock:{lock_name}"
        for _ in range(retry_times):
            if await client.set(lock_key, "1", nx=True, ex=timeout_seconds):
                return True
            import asyncio
            await asyncio.sleep(retry_delay_seconds)
        return False
    except Exception as e:
        logger.warning(f"Lock acquisition error for {lock_name}: {e}")
        return False


async def release_lock(lock_name: str) -> bool:
    """Release a distributed lock"""
    try:
        client = await get_redis()
        lock_key = f"lock:{lock_name}"
        await client.delete(lock_key)
        return True
    except Exception as e:
        logger.warning(f"Lock release error for {lock_name}: {e}")
        return False


class RateLimitContext:
    """Context manager for rate limiting"""

    def __init__(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ):
        self.key = key
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.allowed = False
        self.remaining = max_requests

    async def __aenter__(self) -> "RateLimitContext":
        self.allowed, self.remaining = await rate_limit(
            self.key,
            self.max_requests,
            self.window_seconds,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
