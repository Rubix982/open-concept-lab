import unittest
from unittest.mock import MagicMock

from persistent_memory.core import ArxivPaper, ArxivDownloader

# Curated paper collections
PAPER_COLLECTIONS = {
    "attention_mechanisms": [
        "1706.03762",  # Attention Is All You Need (Transformers)
        "1409.0473",  # Neural Machine Translation (Bahdanau Attention)
        "1508.04025",  # Effective Approaches to Attention (Luong)
    ],
    "rag_systems": [
        "2005.11401",  # RAG: Retrieval-Augmented Generation
        "2002.08909",  # REALM: Retrieval-Augmented Language Model
        "2004.04906",  # DPR: Dense Passage Retrieval
    ],
    "memory_networks": [
        "1410.3916",  # Memory Networks
        "1503.08895",  # End-To-End Memory Networks
        "1606.03126",  # Key-Value Memory Networks
    ],
    "hierarchical_models": [
        "1606.02393",  # Hierarchical Attention Networks
        "1511.06303",  # Hierarchical Recurrent Neural Networks
    ],
}


class TestArxivDownloader(unittest.TestCase):
    def setUp(self):
        self.downloader = ArxivDownloader()

    def test_search(self):
        papers = self.downloader.search("test query", max_results=1)
        self.assertEqual(len(papers), 1)

    def test_search_by_category(self):
        papers = self.downloader.search_by_category("cs.AI", max_results=1)
        self.assertEqual(len(papers), 1)

    def test_get_paper_by_id(self):
        paper = self.downloader.get_paper_by_id("2301.12345")
        self.assertIsNotNone(paper)

    def test_download_pdf(self):
        paper = self.downloader.get_paper_by_id("2301.12345")
        if paper:
            filepath = self.downloader.download_pdf(paper)
            self.assertIsNotNone(filepath)

    def test_extract_text_from_pdf(self):
        paper = self.downloader.get_paper_by_id("2301.12345")
        if paper:
            filepath = self.downloader.download_pdf(paper)
            if filepath:
                text = self.downloader.extract_text_from_pdf(filepath)
                self.assertIsNotNone(text)

    def test_download_and_extract(self):
        paper = self.downloader.get_paper_by_id("2301.12345")
        if paper:
            text = self.downloader.download_and_extract(paper)
            self.assertIsNotNone(text)

    def test_end_to_end_demo(self):
        # Demo
        logging.basicConfig(level=logging.INFO)

        downloader = ArxivDownloader()

        # Search for papers
        print("Searching for 'hierarchical attention' papers...")
        papers = downloader.search("hierarchical attention", max_results=5)

        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            print(f"   arXiv ID: {paper.arxiv_id}")
            print(f"   Categories: {', '.join(paper.categories)}")
            print(f"   Abstract: {paper.abstract[:200]}...")

        # Download first paper
        if papers:
            print("\n\nDownloading first paper...")
            text = downloader.download_and_extract(papers[0])
            if text:
                print(f"Extracted {len(text)} characters")
                print(f"First 500 chars:\n{text[:500]}...")


if __name__ == "__main__":
    unittest.main()
