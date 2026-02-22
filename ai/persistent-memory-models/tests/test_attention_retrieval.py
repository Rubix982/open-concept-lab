import unittest
from unittest.mock import MagicMock

from persistent_memory.core import (
    AttentionWeightedConsolidator,
    AttentionEnhancedRetrieval,
    AttentionDataset,
)
from persistent_memory.stores import PersistentVectorStore


class TestAttentionRetrieval(unittest.TestCase):
    def setUp(self):
        self.consolidator = AttentionWeightedConsolidator()
        self.retriever = AttentionEnhancedRetrieval()
        self.dataset = AttentionDataset()

    def test_consolidator(self):
        self.consolidator.track_attention(1, torch.tensor([0.1, 0.2, 0.3]))
        self.consolidator.consolidate_memories(self.dataset)

    def test_retriever(self):
        self.retriever.retrieve_with_attention("test query")

    def test_dataset(self):
        self.dataset.add_memory("test memory")
        self.dataset.add_query("test query")
        self.dataset.add_attention("test attention")
        self.dataset.get_batch()

    def test_end_to_end_demo(self):
        # Demo
        vs = PersistentVectorStore()
        retrieval = AttentionEnhancedRetrieval(vs)

        query = "Who is Elizabeth Bennet?"
        result = retrieval.retrieve_with_attention(query, k=10, return_attention=True)

        print(f"Query: {query}\n")
        print(f"Selected {len(result['contexts'])} contexts")
        print(f"Metadata: {result['metadata']}\n")

        for i, ctx in enumerate(result["contexts"][:3]):
            print(f"{i + 1}. Attention: {ctx['attention_score']:.3f}")
            print(f"   Text: {ctx['text'][:100]}...")
            if "key_sentence" in ctx:
                print(f"   Key sentence: {ctx['key_sentence'][:80]}...")
            print()


if __name__ == "__main__":
    unittest.main()
