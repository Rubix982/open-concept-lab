import unittest
from unittest.mock import MagicMock, patch

from persistent_memory.core import EnhancedLLM


class TestEnhancedLLM(unittest.TestCase):
    @patch("persistent_memory.core.enhanced_llm.PersistentVectorStore")
    @patch("persistent_memory.core.enhanced_llm.PersistentKnowledgeGraph")
    def setUp(self, mock_kg, mock_vs):
        self.llm = EnhancedLLM()

    def test_chat(self):
        with patch.object(self.llm, "chat", return_value="Hello!"):
            response = self.llm.chat("Hello")
            self.assertIsInstance(response, str)


if __name__ == "__main__":
    unittest.main()
