"""
Integration layer between domain events and caching system.
Provides automatic cache invalidation based on domain events.
"""

from collections.abc import Callable
from datetime import datetime

from services.vocabulary.events import (
    DomainEvent,
    EventType,
    get_event_bus,
)

from .caching import cache_manager
from .config.logging_config import get_logger

logger = get_logger(__name__)


class CacheInvalidationHandler:
    """Handles cache invalidation based on domain events"""

    def __init__(self):
        self.invalidation_rules: dict[EventType, list[Callable]] = {}
        self._setup_invalidation_rules()
        self._register_handlers()

    def _setup_invalidation_rules(self):
        """Setup cache invalidation rules for different event types"""
        self.invalidation_rules = {
            EventType.WORD_LEARNED: [
                self._invalidate_user_progress,
                self._invalidate_user_stats,
                self._invalidate_vocabulary_word,
            ],
            EventType.WORD_MASTERED: [
                self._invalidate_user_progress,
                self._invalidate_user_stats,
                self._invalidate_level_progress,
            ],
            EventType.PROGRESS_UPDATED: [self._invalidate_user_progress, self._invalidate_user_stats],
            EventType.VOCABULARY_ADDED: [self._invalidate_vocabulary_cache, self._invalidate_level_cache],
            EventType.STREAK_ACHIEVED: [self._invalidate_user_stats],
            EventType.LEVEL_COMPLETED: [self._invalidate_user_progress, self._invalidate_level_progress],
        }

    def _register_handlers(self):
        """Register event handlers with the event bus"""
        event_bus = get_event_bus()
        for event_type in self.invalidation_rules:
            event_bus.register_handler(event_type, self.handle_cache_invalidation)

    async def handle_cache_invalidation(self, event: DomainEvent):
        """Handle cache invalidation for domain events"""
        try:
            if event.event_type is None:
                logger.warning("Event has no event_type, skipping cache invalidation")
                return

            handlers = self.invalidation_rules.get(event.event_type, [])
            for handler in handlers:
                await handler(event)

            logger.debug("Cache invalidated", event_type=event.event_type)
        except Exception as e:
            logger.error("Cache invalidation error", event_type=event.event_type, error=str(e))

    async def _invalidate_user_progress(self, event: DomainEvent):
        """Invalidate user progress cache"""
        if hasattr(event, "user_id") and event.user_id:
            # Invalidate user-specific progress cache
            await cache_manager.delete(f"user_progress:user:{event.user_id}")
            await cache_manager.delete(f"progress:user:{event.user_id}:de")
            await cache_manager.delete(f"progress:user:{event.user_id}:en")

    async def _invalidate_user_stats(self, event: DomainEvent):
        """Invalidate user statistics cache"""
        if hasattr(event, "user_id") and event.user_id:
            await cache_manager.delete(f"user_stats:user:{event.user_id}")
            await cache_manager.delete(f"vocabulary_stats:user:{event.user_id}")

    async def _invalidate_vocabulary_word(self, event: DomainEvent):
        """Invalidate vocabulary word cache"""
        if hasattr(event, "vocabulary_word") and event.vocabulary_word:
            word_id = event.vocabulary_word.id
            if word_id:
                await cache_manager.delete(f"vocabulary:word:{word_id}")

    async def _invalidate_vocabulary_cache(self, event: DomainEvent):
        """Invalidate general vocabulary cache"""
        await cache_manager.clear_domain("vocabulary")

    async def _invalidate_level_cache(self, event: DomainEvent):
        """Invalidate level-specific cache"""
        if hasattr(event, "difficulty_level"):
            level = event.difficulty_level.value if hasattr(event.difficulty_level, "value") else event.difficulty_level
            await cache_manager.delete(f"vocabulary:level:{level}")

    async def _invalidate_level_progress(self, event: DomainEvent):
        """Invalidate level progress cache"""
        if hasattr(event, "user_id") and hasattr(event, "difficulty_level"):
            user_id = event.user_id
            level = event.difficulty_level.value if hasattr(event.difficulty_level, "value") else event.difficulty_level
            await cache_manager.delete(f"level_progress:user:{user_id}:level:{level}")


class EventDrivenCacheManager:
    """Enhanced cache manager with event-driven invalidation"""

    def __init__(self):
        self.cache_handler = CacheInvalidationHandler()
        self.cache_stats = {"hits": 0, "misses": 0, "invalidations": 0, "last_reset": datetime.utcnow()}

    async def get_with_stats(self, key: str, domain: str = "default"):
        """Get from cache with hit/miss statistics"""
        value = await cache_manager.get(key, domain)
        if value is not None:
            self.cache_stats["hits"] += 1
        else:
            self.cache_stats["misses"] += 1
        return value

    async def set_with_metadata(self, key: str, value, domain: str = "default", metadata: dict | None = None):
        """Set cache with metadata for better invalidation"""
        enriched_value = {"data": value, "metadata": metadata or {}, "cached_at": datetime.utcnow().isoformat()}
        return await cache_manager.set(key, enriched_value, domain)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        count = await cache_manager.clear_domain(pattern)
        self.cache_stats["invalidations"] += count
        return count

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {**self.cache_stats, "hit_rate_percent": round(hit_rate, 2), "total_requests": total_requests}

    def reset_stats(self):
        """Reset cache statistics"""
        self.cache_stats = {"hits": 0, "misses": 0, "invalidations": 0, "last_reset": datetime.utcnow()}


# Global instance
event_driven_cache = EventDrivenCacheManager()


def setup_event_cache_integration():
    """Setup event-driven cache integration"""
    logger.info("Setting up event-driven cache integration")
    # The CacheInvalidationHandler automatically registers itself
    return event_driven_cache


# Decorator for automatic cache invalidation on events
def invalidate_on_events(*event_types: EventType):
    """Decorator to automatically invalidate cache on specific events"""

    def decorator(func):
        # This would require more complex implementation
        # For now, just return the function unchanged
        return func

    return decorator


# Health check for the integrated system
async def cache_event_health_check() -> dict:
    """Health check for cache and event integration"""
    cache_health = await cache_manager.health_check()
    event_bus = get_event_bus()

    return {
        "cache": cache_health,
        "event_bus": {
            "handlers_registered": len(event_driven_cache.cache_handler.invalidation_rules),
            "events_processed": len(event_bus.get_events()),
        },
        "integration": {"status": "active", "cache_stats": event_driven_cache.get_cache_stats()},
    }
