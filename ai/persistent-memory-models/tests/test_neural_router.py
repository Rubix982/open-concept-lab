import unittest

import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from persistent_memory.core.context_router import ContextRouter


class TestNeuralRouter(unittest.TestCase):
    def setUp(self):
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

        probs = self.router.router.predict(embedding)
        self.assertEqual(len(probs), 4)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=5)

    @unittest.skipUnless(HAS_TORCH, "torch not available")
    def test_router_update_learning(self):
        """Verify that the router weights change after an update."""
        embedding = np.random.randn(1536).astype(np.float32)

        initial_params = [p.clone() for p in self.router.router.parameters()]

        self.router.update(embedding, reward=1.0)

        for p_initial, p_final in zip(initial_params, self.router.router.parameters()):
            self.assertFalse(
                torch.equal(p_initial, p_final),
                "Weights should have changed after update",
            )

    def test_route_query_integration(self):
        """Integration test for route_query."""
        embedding = np.random.randn(1536).astype(np.float32)
        results = self.router.route_query("test query", query_embedding=embedding)
        self.assertTrue(isinstance(results, list))


if __name__ == "__main__":
    unittest.main()
