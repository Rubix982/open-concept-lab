import unittest
from unittest.mock import MagicMock
import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any
from persistent_memory.processors import StreamingQueryEngine

logger = logging.getLogger(__name__)


class TestStreamingQueryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = StreamingQueryEngine()

    def test_query(self):
        """Test query."""
        result = self.engine.query("test")
        self.assertIsNotNone(result)

    async def test_end_to_end_demo(self):
        """Demo streaming query."""
        engine = StreamingQueryEngine()

        print("Streaming query: 'Who is Elizabeth Bennet?'\n")

        async for chunk in engine.stream_query("Who is Elizabeth Bennet?"):
            chunk_type = chunk["type"]
            data = chunk["data"]

            if chunk_type == "status":
                print(f"📊 {data['message']} ({data['progress'] * 100:.0f}%)")
            elif chunk_type == "vector_result":
                print(f"📄 Vector result {data['index']}: {data['text'][:100]}...")
            elif chunk_type == "graph_result":
                print(
                    f"🔗 Graph: {data['subject']} → {data['predicate']} → {data['object']}"
                )
            elif chunk_type == "answer":
                print(f"\n💡 Answer: {data['text']}\n")
            elif chunk_type == "complete":
                print(f"✅ Complete! Stats: {data['stats']}")


if __name__ == "__main__":
    unittest.main()
