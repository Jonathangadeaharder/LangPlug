"""Cache dependencies"""

from core.cache.redis_client import RedisCacheClient, redis_cache


def get_redis_client() -> RedisCacheClient:
    """
    Get the Redis cache client instance.

    Returns:
        RedisCacheClient: Global Redis cache client
    """
    return redis_cache
