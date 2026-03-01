import unittest
from unittest.mock import MagicMock, patch

import pytest

try:
    import torch
    import numpy as np
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from persistent_memory.core import HierarchicalAttentionNetwork

if HAS_TORCH:
    from persistent_memory.core import AttentionConfig


class TestHierarchicalAttentionNetwork(unittest.TestCase):
    def setUp(self):
        if not HAS_TORCH:
            self.skipTest("torch not available")
        self.attention_network = HierarchicalAttentionNetwork()

    def test_forward(self):
        response = self.attention_network.forward("Hello")
        self.assertIsInstance(response, str)

    @pytest.mark.skipif(not HAS_TORCH, reason="torch not available")
    def test_end_to_end_demo(self) -> None:
        config = AttentionConfig()
        model = HierarchicalAttentionNetwork(config)

        batch_size = 2
        query_emb = torch.randn(batch_size, config.embedding_dim)
        chunk_embs = torch.randn(batch_size, 10, config.embedding_dim)
        sentence_embs = torch.randn(batch_size, 50, config.embedding_dim)

        outputs = model(query_emb, chunk_embs, sentence_embs)

        assert isinstance(outputs, dict)


if __name__ == "__main__":
    unittest.main()
