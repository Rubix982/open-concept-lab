import unittest
from unittest.mock import MagicMock

from persistent_memory.processors import StreamingQueryEngine


class TestStreamingQueryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = StreamingQueryEngine()

    def test_query(self):
        """Test query."""
        result = self.engine.query("test")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
