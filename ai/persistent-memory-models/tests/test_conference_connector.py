import unittest
from unittest.mock import MagicMock, patch

from persistent_memory.core import (
    Conference,
    ConferenceConnector,
)


class TestConferenceConnector(unittest.TestCase):
    def setUp(self):
        self.connector = ConferenceConnector()

    @patch.object(ConferenceConnector, "list_conferences")
    def test_list_conferences(self, mock_list):
        mock_list.return_value = [{"name": "neurips", "full_name": "NeurIPS"}]
        conferences = self.connector.list_conferences()
        self.assertIsInstance(conferences, list)
        self.assertGreater(len(conferences), 0)

    @patch.object(ConferenceConnector, "get_conference_papers")
    def test_get_conference_papers(self, mock_get):
        mock_get.return_value = [MagicMock()]
        papers = self.connector.get_conference_papers("neurips", max_results=3)
        self.assertIsInstance(papers, list)
        self.assertGreater(len(papers), 0)


if __name__ == "__main__":
    unittest.main()
