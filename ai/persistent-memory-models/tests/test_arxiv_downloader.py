import unittest
from unittest.mock import MagicMock, patch

from persistent_memory.core import ArxivPaper, ArxivDownloader


class TestArxivDownloader(unittest.TestCase):
    def setUp(self):
        self.downloader = ArxivDownloader()

    @patch.object(ArxivDownloader, "search")
    def test_search(self, mock_search):
        mock_search.return_value = [MagicMock(spec=ArxivPaper)]
        papers = self.downloader.search("test query", max_results=1)
        self.assertEqual(len(papers), 1)

    @patch.object(ArxivDownloader, "search_by_category")
    def test_search_by_category(self, mock_search):
        mock_search.return_value = [MagicMock(spec=ArxivPaper)]
        papers = self.downloader.search_by_category("cs.AI", max_results=1)
        self.assertEqual(len(papers), 1)

    @patch.object(ArxivDownloader, "get_paper_by_id")
    def test_get_paper_by_id(self, mock_get):
        mock_get.return_value = MagicMock(spec=ArxivPaper)
        paper = self.downloader.get_paper_by_id("2301.12345")
        self.assertIsNotNone(paper)

    @patch.object(ArxivDownloader, "download_and_extract")
    @patch.object(ArxivDownloader, "get_paper_by_id")
    def test_download_and_extract(self, mock_get, mock_extract):
        mock_paper = MagicMock(spec=ArxivPaper)
        mock_get.return_value = mock_paper
        mock_extract.return_value = "extracted text"

        paper = self.downloader.get_paper_by_id("2301.12345")
        if paper:
            text = self.downloader.download_and_extract(paper)
            self.assertIsNotNone(text)


if __name__ == "__main__":
    unittest.main()
