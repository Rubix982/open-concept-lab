import unittest
from unittest.mock import MagicMock

from persistent_memory.core import (
    Conference,
    ConferenceConnector,
)


class TestConferenceConnector(unittest.TestCase):
    def setUp(self):
        self.connector = ConferenceConnector()

    def test_list_conferences(self):
        conferences = self.connector.list_conferences()
        self.assertIsInstance(conferences, list)
        self.assertGreater(len(conferences), 0)

    def test_get_conference_papers(self):
        papers = self.connector.get_conference_papers("neurips", max_results=3)
        self.assertIsInstance(papers, list)
        self.assertGreater(len(papers), 0)

    def test_end_to_end_demo(self):
        # Demo
        logging.basicConfig(level=logging.INFO)
        connector = ConferenceConnector()

        print("Supported Conferences:")
        for conf in connector.list_conferences():
            print(f"- {conf['name']} ({conf['full_name']})")

        print("\nFetching recent NeurIPS papers...")
        papers = connector.get_conference_papers("neurips", max_results=3)

        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            print(f"   arXiv: {paper.arxiv_id}")


if __name__ == "__main__":
    unittest.main()
