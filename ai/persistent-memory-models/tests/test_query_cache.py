import unittest
from unittest.mock import MagicMock, patch
import json

from persistent_memory.stores.query_cache import QueryCache


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


if __name__ == "__main__":
    unittest.main()
