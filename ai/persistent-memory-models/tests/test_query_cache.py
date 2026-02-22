import unittest
from unittest.mock import MagicMock
import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis
from src.persistent_memory.stores.query_cache import QueryCache

logger = logging.getLogger(__name__)


class TestQueryCache(unittest.TestCase):
    def setUp(self):
        self.cache = QueryCache()
        self.cache.client = MagicMock()

    def test_make_key(self):
        key = self.cache._make_key("test query", k=5)
        self.assertIn("query:", key)

    def test_get(self):
        self.cache.client.get.return_value = json.dumps({"results": []})
        result = self.cache.get("test query", k=5)
        self.assertEqual(result, {"results": []})

    def test_set(self):
        self.cache.set("test query", {"results": []}, k=5)
        self.cache.client.setex.assert_called_once()

    def test_invalidate(self):
        self.cache.invalidate("test query", k=5)
        self.cache.client.delete.assert_called_once()

    def test_invalidate_pattern(self):
        self.cache.invalidate_pattern("test_pattern")
        self.cache.client.keys.assert_called_once_with("query:test_pattern")

    def test_get_stats(self):
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["hit_rate"], 0)
        self.assertEqual(stats["enabled"], True)

    async def test_end_to_end_demo(self):
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
    unittest.main()
