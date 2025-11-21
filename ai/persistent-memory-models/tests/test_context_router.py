import unittest
from unittest.mock import MagicMock
from persistent_memory.context_router import ContextRouter

class TestContextRouter(unittest.TestCase):
    def setUp(self):
        # Mock layers
        self.working = MagicMock()
        self.episodic = MagicMock()
        self.semantic = MagicMock()
        self.archive = MagicMock()
        
        self.working.get_current_context.return_value = ["working_context"]
        self.episodic.search.return_value = [{"text": "episodic_result", "distance": 0.1}]
        self.semantic.query.return_value = [{"text": "semantic_result", "distance": 0.2}]
        self.archive.retrieve.return_value = [{"text": "archive_result", "distance": 0.3}]
        
        self.router = ContextRouter([self.working, self.episodic, self.semantic, self.archive])

    def test_routing(self):
        # Mock router network to return high probability for all layers
        self.router.router = MagicMock(return_value=[0.1, 0.4, 0.4, 0.3])
        
        results = self.router.route_query("test query")
        
        # Check if all layers were queried
        self.working.get_current_context.assert_called()
        self.episodic.search.assert_called()
        self.semantic.query.assert_called()
        self.archive.retrieve.assert_called()
        
        # Check results structure
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]['layer'], 'working') # working memory usually ranked high due to recency mock

if __name__ == '__main__':
    unittest.main()
