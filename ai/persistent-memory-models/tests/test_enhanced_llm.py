import unittest
from unittest.mock import MagicMock

from persistent_memory.core import EnhancedLLM


class TestEnhancedLLM(unittest.TestCase):
    def setUp(self):
        self.llm = EnhancedLLM()

    def test_chat(self):
        response = self.llm.chat("Hello")
        self.assertIsInstance(response, str)

    # ============================================================================
    # Demo / Example Usage
    # ============================================================================
    def test_end_to_end_demo(self):
        """Demo the Enhanced LLM."""
        print("\n" + "🤖" * 40)
        print("Enhanced LLM Demo - Chatbot with Persistent Memory")
        print("🤖" * 40)

        # Initialize
        print("\n🚀 Initializing Enhanced LLM...")
        bot = EnhancedLLM(
            model="mistral",
            enable_cache=True,
            enable_attention=True,
            enable_quality_monitoring=True,
        )

        # Teach it something
        print("\n📖 Teaching the bot about transformers...")
        await bot.teach(
            "Transformers are neural network architectures that use self-attention mechanisms. "
            "They were introduced in the 'Attention is All You Need' paper in 2017. "
            "Key components include multi-head attention, positional encodings, and feed-forward networks.",
            source="training",
        )

        # Chat
        print("\n💬 Starting conversation...")

        queries = [
            "What are transformers?",
            "When were they introduced?",
            "What are the key components?",
        ]

        for query in queries:
            print(f"\n👤 User: {query}")
            result = await bot.chat(query, return_metadata=True)
            print(f"🤖 Bot: {result['response']}")
            print(f"   ⏱️  Latency: {result['latency']:.2f}s")
            print(f"   📚 Contexts used: {result['contexts_used']}")
            if result.get("quality_metrics"):
                print(
                    f"   📊 Quality: {result['quality_metrics']['relevance_score']:.3f}"
                )

        # Show stats
        print("\n📊 Bot Statistics:")
        stats = bot.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print("\n✅ Demo complete!")


if __name__ == "__main__":
    unittest.main()
