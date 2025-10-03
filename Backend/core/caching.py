"""
Enhanced multi-level caching layer implementation
Provides in-memory, Redis, and domain-specific caching strategies
"""

import hashlib
import json
import logging
import pickle  # nosec B403
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CacheKey:
    """Structured cache key with metadata"""

    namespace: str
    identifier: str
    version: str = "v1"
    params_hash: str | None = None

    def __str__(self) -> str:
        parts = [self.namespace, self.identifier, self.version]
        if self.params_hash:
            parts.append(self.params_hash)
        return ":".join(parts)

    @classmethod
    def from_function(cls, func: Callable, *args, **kwargs) -> "CacheKey":
        """Create cache key from function and parameters"""
        namespace = f"{func.__module__}.{func.__name__}"
        identifier = func.__name__

        # Create hash of parameters (MD5 is acceptable for cache keys, not security)
        params_data = {"args": args, "kwargs": kwargs}
        params_json = json.dumps(params_data, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_json.encode(), usedforsecurity=False).hexdigest()[:8]

        return cls(namespace=namespace, identifier=identifier, params_hash=params_hash)


class CacheBackend(ABC):
    """Abstract base class for cache backends"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        pass


class InMemoryCache(CacheBackend):
    """Enhanced in-memory cache with TTL and LRU eviction"""

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, Any] = {}
        self._ttl: dict[str, datetime] = {}
        self._access_order: list[str] = []
        self.max_size = max_size

    async def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None

        # Check TTL
        if key in self._ttl and datetime.utcnow() > self._ttl[key]:
            await self.delete(key)
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return self._cache[key]

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        # Evict if cache is full
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict_lru()

        self._cache[key] = value

        if ttl:
            self._ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return True

    async def delete(self, key: str) -> bool:
        deleted = key in self._cache
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)
        return deleted

    async def clear_pattern(self, pattern: str) -> int:
        keys_to_delete = [k for k in self._cache if pattern in k]
        for key in keys_to_delete:
            await self.delete(key)
        return len(keys_to_delete)

    async def _evict_lru(self):
        """Evict least recently used item"""
        if self._access_order:
            lru_key = self._access_order[0]
            await self.delete(lru_key)


class EnhancedCacheManager:
    """Enhanced multi-level cache manager with domain-specific strategies"""

    def __init__(self):
        self._memory_cache = InMemoryCache(max_size=2000)
        self._redis_client = None
        self._domain_caches: dict[str, dict[str, Any]] = {}
        self._setup_redis()
        self._setup_domain_caches()

    def _setup_redis(self):
        """Setup Redis connection if available"""
        if REDIS_AVAILABLE and settings.redis_url:
            try:
                self._redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=False,  # Handle binary data
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis cache backend initialized")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory cache: {e}")
                self._redis_client = None

    def _setup_domain_caches(self):
        """Setup domain-specific cache configurations"""
        self._domain_caches = {
            "vocabulary": {
                "l1_ttl": 3600,  # 1 hour in memory
                "l2_ttl": 86400,  # 24 hours in Redis
                "max_size": 2000,
            },
            "user_progress": {
                "l1_ttl": 1800,  # 30 minutes in memory
                "l2_ttl": 7200,  # 2 hours in Redis
                "max_size": 1000,
            },
            "sessions": {
                "l1_ttl": 600,  # 10 minutes in memory
                "l2_ttl": 3600,  # 1 hour in Redis
                "max_size": 500,
            },
        }

    async def get(self, key: str, domain: str = "default") -> Any | None:
        """Get value from multi-level cache"""
        # Try L1 (memory) first
        value = await self._memory_cache.get(key)
        if value is not None:
            return value

        # Try L2 (Redis) if available
        if self._redis_client:
            try:
                redis_value = self._redis_client.get(key)
                if redis_value:
                    # Deserialize and back-fill L1
                    # nosec B301: pickle is safe here - Redis is internal trusted cache
                    deserialized = pickle.loads(redis_value)  # noqa: S301  # nosec
                    config = self._domain_caches.get(domain, {"l1_ttl": 300})
                    await self._memory_cache.set(key, deserialized, config["l1_ttl"])
                    return deserialized
            except Exception as e:
                logger.debug(f"Redis get failed for {key}: {e}")

        return None

    async def set(self, key: str, value: Any, domain: str = "default", expire: int | None = None) -> bool:
        """Set value in multi-level cache"""
        config = self._domain_caches.get(domain, {"l1_ttl": 300, "l2_ttl": 3600})

        # Set in L1 (memory)
        l1_ttl = expire or config["l1_ttl"]
        l1_success = await self._memory_cache.set(key, value, l1_ttl)

        # Set in L2 (Redis) if available
        l2_success = True
        if self._redis_client:
            try:
                # nosec B301: pickle is safe for internal trusted Redis cache
                serialized = pickle.dumps(value)  # nosec
                l2_ttl = expire or config["l2_ttl"]
                l2_success = self._redis_client.set(key, serialized, ex=l2_ttl)
            except Exception as e:
                logger.debug(f"Redis set failed for {key}: {e}")
                l2_success = False

        return l1_success or l2_success

    async def delete(self, key: str) -> bool:
        """Delete key from both cache levels"""
        l1_result = await self._memory_cache.delete(key)
        l2_result = True

        if self._redis_client:
            try:
                l2_result = bool(self._redis_client.delete(key))
            except Exception as e:
                logger.debug(f"Redis delete failed for {key}: {e}")
                l2_result = False

        return l1_result or l2_result

    async def clear_domain(self, domain: str) -> int:
        """Clear all cache entries for a domain"""
        pattern = f"{domain}:"
        l1_count = await self._memory_cache.clear_pattern(pattern)
        l2_count = 0

        if self._redis_client:
            try:
                keys = self._redis_client.keys(f"{pattern}*")
                if keys:
                    l2_count = self._redis_client.delete(*keys)
            except Exception as e:
                logger.debug(f"Redis clear domain failed for {domain}: {e}")

        return l1_count + l2_count

    async def health_check(self) -> dict[str, Any]:
        """Health check for cache system"""
        health = {
            "status": "healthy",
            "memory_cache": {"size": len(self._memory_cache._cache), "max_size": self._memory_cache.max_size},
            "redis_cache": None,
        }

        if self._redis_client:
            try:
                self._redis_client.ping()
                info = self._redis_client.info()
                health["redis_cache"] = {
                    "status": "connected",
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                }
            except Exception as e:
                health["redis_cache"] = {"status": "error", "error": str(e)}
                health["status"] = "degraded"

        return health


# Global enhanced cache manager instance
cache_manager = EnhancedCacheManager()


# Legacy cache manager for backward compatibility
class CacheManager(EnhancedCacheManager):
    """Legacy cache manager for backward compatibility"""

    def get(self, key: str) -> Any | None:
        """Synchronous get method for backward compatibility"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get(key))
        except RuntimeError:
            # No event loop running, use simplified approach
            return self._memory_cache._cache.get(key)

    def set(self, key: str, value: Any, expire: int | timedelta | None = None) -> bool:
        """Synchronous set method for backward compatibility"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            expire_seconds = expire.total_seconds() if isinstance(expire, timedelta) else expire
            return loop.run_until_complete(self.set(key, value, expire=int(expire_seconds) if expire_seconds else None))
        except RuntimeError:
            # No event loop running, use simplified approach
            self._memory_cache._cache[key] = value
            return True


def cache_result(key_prefix: str, expire: int | timedelta | None = None):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, expire)
            return result

        return wrapper

    return decorator


# Convenience functions for common cache operations
def cache_vocabulary_word(word_id: int, data: dict, expire: int = 3600):
    """Cache vocabulary word data"""
    cache_manager.set(f"vocabulary:word:{word_id}", data, expire)


def get_cached_vocabulary_word(word_id: int) -> dict | None:
    """Get cached vocabulary word data"""
    return cache_manager.get(f"vocabulary:word:{word_id}")


def cache_user_progress(user_id: int, language: str, data: dict, expire: int = 1800):
    """Cache user vocabulary progress"""
    cache_manager.set(f"progress:user:{user_id}:{language}", data, expire)


def get_cached_user_progress(user_id: int, language: str) -> dict | None:
    """Get cached user vocabulary progress"""
    return cache_manager.get(f"progress:user:{user_id}:{language}")


def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a user"""
    # This is simplified - in production you'd use pattern matching
    cache_manager.delete(f"progress:user:{user_id}:de")
    cache_manager.delete(f"progress:user:{user_id}:en")
    cache_manager.delete(f"progress:user:{user_id}:es")
