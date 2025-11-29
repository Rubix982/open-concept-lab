"""Query result caching with Redis for performance."""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class QueryCache:
    """
    Cache query results to avoid expensive re-computation.

    Features:
    - TTL-based expiration
    - LRU eviction
    - Cache invalidation
    - Hit/miss metrics
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,  # 1 hour
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.client: redis.Redis | None = None

        # Metrics
        self.hits = 0
        self.misses = 0

        logger.info(f"Initialized QueryCache with TTL={default_ttl}s")

    async def connect(self):
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.client = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()

    def _make_key(self, query: str, **kwargs) -> str:
        """Create cache key from query and parameters."""
        # Include query + all kwargs in key
        key_data = {"query": query, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True)

        # Hash for consistent length
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]

        return f"query:{key_hash}"

    async def get(self, query: str, **kwargs) -> dict[str, Any] | None:
        """
        Get cached query result.

        Args:
            query: The search query
            **kwargs: Additional parameters (k, filters, etc.)

        Returns:
            Cached result or None if not found
        """
        if not self.client:
            return None

        key = self._make_key(query, **kwargs)

        try:
            cached = await self.client.get(key)

            if cached:
                self.hits += 1
                logger.debug(f"Cache HIT for query: {query[:50]}")
                return json.loads(cached)
            else:
                self.misses += 1
                logger.debug(f"Cache MISS for query: {query[:50]}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, query: str, result: dict[str, Any], ttl: int | None = None, **kwargs):
        """
        Cache query result.

        Args:
            query: The search query
            result: The result to cache
            ttl: Time to live in seconds (None = use default)
            **kwargs: Additional parameters used in query
        """
        if not self.client:
            return

        key = self._make_key(query, **kwargs)
        ttl = ttl or self.default_ttl

        try:
            # Handle non-dict results (e.g. string response)
            if not isinstance(result, dict):
                result = {"value": result, "type": str(type(result).__name__)}

            await self.client.setex(key, ttl, json.dumps(result))
            logger.debug(f"Cached result for query: {query[:50]} (TTL={ttl}s)")

        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def invalidate(self, query: str, **kwargs):
        """Invalidate cached result for a query."""
        if not self.client:
            return

        key = self._make_key(query, **kwargs)

        try:
            await self.client.delete(key)
            logger.debug(f"Invalidated cache for query: {query[:50]}")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")

    async def invalidate_pattern(self, pattern: str = "*"):
        """Invalidate all keys matching pattern."""
        if not self.client:
            return

        try:
            keys = await self.client.keys(f"query:{pattern}")
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cached queries")
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "enabled": self.client is not None,
        }


class CachedVectorStore:
    """Vector store with automatic caching."""

    def __init__(self, vector_store, cache: QueryCache):
        self.vector_store = vector_store
        self.cache = cache

    async def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search with caching."""
        # Try cache first
        cached = await self.cache.get(query, k=k)
        if cached is not None:
            return cached

        # Cache miss - do actual search
        results = self.vector_store.search(query, k=k)

        # Cache for future
        await self.cache.set(query, results, k=k)

        return results


# Example usage
async def demo_caching():
    """Demo query caching."""
    cache = QueryCache(redis_url="redis://localhost:6379")
    await cache.connect()

    # Simulate queries
    query = "Who is Elizabeth Bennet?"

    # First query (cache miss)
    result1 = await cache.get(query, k=5)
    print(f"First query: {result1}")  # None

    # Cache the result
    await cache.set(query, {"results": ["mock data"]}, k=5)

    # Second query (cache hit)
    result2 = await cache.get(query, k=5)
    print(f"Second query: {result2}")  # {"results": ["mock data"]}

    # Stats
    print(f"Cache stats: {cache.get_stats()}")

    await cache.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_caching())
