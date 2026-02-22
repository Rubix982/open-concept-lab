import unittest
import numpy as np
import torch
from persistent_memory.context_router import ContextRouter


class TestNeuralRouter(unittest.TestCase):
    def setUp(self):
        # Mock layers
        self.working = type("Mock", (), {"get_current_context": lambda: []})()
        self.episodic = type("Mock", (), {"search": lambda query, k: []})()
        self.semantic = type("Mock", (), {"query": lambda query: []})()
        self.archive = type("Mock", (), {"retrieve": lambda query, k: []})()

        self.router = ContextRouter(
            [self.working, self.episodic, self.semantic, self.archive]
        )

    def test_routing_prediction(self):
        query = "test query"
        embedding = np.random.randn(1536).astype(np.float32)

        # Test that predict returns probabilities summing to 1
        probs = self.router.router.predict(embedding)
        self.assertEqual(len(probs), 4)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=5)

    def test_router_update_learning(self):
        """Verify that the router weights change after an update."""
        embedding = np.random.randn(1536).astype(np.float32)

        # Get initial weights
        initial_params = [p.clone() for p in self.router.router.parameters()]

        # Perform update with high reward
        self.router.update(embedding, reward=1.0)

        # Check that weights have changed
        for p_initial, p_final in zip(initial_params, self.router.router.parameters()):
            self.assertFalse(
                torch.equal(p_initial, p_final),
                "Weights should have changed after update",
            )

    async def test_route_query_integration(self):
        """Integration test for route_query."""
        embedding = np.random.randn(1536).astype(np.float32)
        results = await self.router.route_query("test query", query_embedding=embedding)

        # Should at least return working memory (always queried)
        self.assertTrue(isinstance(results, list))


if __name__ == "__main__":
    unittest.main()
