import unittest
from unittest.mock import MagicMock, patch

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from persistent_memory.core import (
    AttentionWeightedConsolidator,
    AttentionEnhancedRetrieval,
    AttentionDataset,
)


class TestAttentionRetrieval(unittest.TestCase):
    def setUp(self):
        self.mock_model = MagicMock()
        self.consolidator = AttentionWeightedConsolidator(self.mock_model)
        self.mock_vs = MagicMock()
        self.mock_vs.search.return_value = [
            {"text": "test result", "distance": 0.1, "id": "1"}
        ]
        self.retriever = AttentionEnhancedRetrieval(self.mock_vs)
        self.dataset = AttentionDataset()

    @unittest.skipUnless(HAS_TORCH, "torch not available")
    def test_consolidator(self):
        self.consolidator.track_attention(1, torch.tensor([0.1, 0.2, 0.3]))

    def test_retriever(self):
        result = self.retriever.retrieve_with_attention("test query")
        self.assertIsNotNone(result)

    def test_dataset(self):
        self.dataset.add_example(
            query="test query",
            contexts=["ctx1"],
            relevance_scores=[0.9],
        )
        self.assertEqual(len(self.dataset.examples), 1)

    def test_end_to_end_demo(self):
        retrieval = AttentionEnhancedRetrieval(self.mock_vs)
        query = "Who is Elizabeth Bennet?"
        result = retrieval.retrieve_with_attention(query, k=10, return_attention=True)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
