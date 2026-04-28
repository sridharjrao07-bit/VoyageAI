"""
Generic Redis Caching Decorator for External API Calls

Usage:
    from engine.redis_cache import redis_cache

    @redis_cache(prefix="weather", ttl=3600)
    async def get_current_weather(lat: float, lon: float) -> dict:
        ...

The decorator serialises function arguments into a cache key and stores
the JSON-serialised return value in Redis with the specified TTL (default 1 hour).
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
from typing import Any, Callable

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Lazy-initialise and return a shared async Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis_pool


async def close_redis() -> None:
    """Gracefully close the Redis pool (call on app shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


def redis_cache(prefix: str, ttl: int = 3600) -> Callable:
    """
    Decorator factory.

    Parameters
    ----------
    prefix : str
        Namespace prefix for the cache key, e.g. ``"weather"`` or ``"flights"``.
    ttl : int
        Time-to-live in seconds (default **3600** = 1 hour).
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build a deterministic cache key from the function args
            key_data = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            cache_key = f"allora:{prefix}:{key_hash}"

            try:
                r = await get_redis()
                cached = await r.get(cache_key)
                if cached is not None:
                    print(f"[RedisCache] HIT  {prefix} {cache_key[-8:]}")
                    return json.loads(cached)
            except Exception as exc:
                # Redis unavailable — fall through to the real function
                print(f"[RedisCache] Redis error (GET): {exc}")

            # Cache miss — call the real function
            result = await fn(*args, **kwargs)

            try:
                r = await get_redis()
                await r.setex(cache_key, ttl, json.dumps(result, default=str))
                print(f"[RedisCache] SET  {prefix} {cache_key[-8:]} ttl={ttl}s")
            except Exception as exc:
                print(f"[RedisCache] Redis error (SET): {exc}")

            return result

        return wrapper

    return decorator
