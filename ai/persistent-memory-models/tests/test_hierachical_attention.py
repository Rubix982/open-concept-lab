import unittest
from unittest.mock import MagicMock

from persistent_memory.core import HierarchicalAttentionNetwork


class TestHierarchicalAttentionNetwork(unittest.TestCase):
    def setUp(self):
        self.attention_network = HierarchicalAttentionNetwork()

    def test_forward(self):
        response = self.attention_network.forward("Hello")
        self.assertIsInstance(response, str)

    def test_end_to_end_demo(self) -> None:
        # Demo
        config = AttentionConfig()
        model = HierarchicalAttentionNetwork(config)

        # Dummy data
        batch_size = 2
        query_emb = torch.randn(batch_size, config.embedding_dim)
        chunk_embs = torch.randn(batch_size, 10, config.embedding_dim)
        sentence_embs = torch.randn(batch_size, 50, config.embedding_dim)

        outputs = model(query_emb, chunk_embs, sentence_embs)

        print("Output shapes:")
        for k, v in outputs.items():
            print(f"  {k}: {v.shape}")

        print("\nAttention weights:")
        weights = model.get_attention_weights(outputs)
        print(f"  Chunk attention: {weights['chunk_attention'][0]}")
        print(f"  Top 3 chunks: {np.argsort(weights['chunk_attention'][0])[-3:]}")


if __name__ == "__main__":
    unittest.main()
