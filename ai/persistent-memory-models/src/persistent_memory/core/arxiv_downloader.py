"""
arXiv Paper Downloader and Processor.

Downloads research papers from arXiv.org and extracts text content.
"""

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import feedparser
import PyPDF2
import requests

logger = logging.getLogger(__name__)


@dataclass
class ArxivPaper:
    """Metadata for an arXiv paper."""

    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: str
    pdf_url: str
    arxiv_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "categories": self.categories,
            "published": self.published,
            "pdf_url": self.pdf_url,
            "arxiv_url": self.arxiv_url,
        }


class ArxivDownloader:
    """
    Download and process papers from arXiv.org.

    Features:
    - Search by keywords, authors, categories
    - Download PDFs
    - Extract text from PDFs
    - Rate limiting to respect arXiv API
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, rate_limit_seconds: float = 3.0):
        """
        Args:
            rate_limit_seconds: Seconds to wait between API calls
        """
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        logger.info(
            f"Initialized ArxivDownloader with rate limit: {rate_limit_seconds}s"
        )

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> list[ArxivPaper]:
        """
        Search arXiv for papers.

        Args:
            query: Search query (e.g., "attention mechanism", "cat:cs.AI")
            max_results: Maximum number of results
            sort_by: Sort by 'relevance', 'lastUpdatedDate', 'submittedDate'
            sort_order: 'ascending' or 'descending'

        Returns:
            List of ArxivPaper objects
        """
        self._rate_limit()

        params: dict[str, str | int] = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            papers = []
            for entry in feed.entries:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)

            logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []

    def search_by_category(
        self, category: str, max_results: int = 10
    ) -> list[ArxivPaper]:
        """
        Search by arXiv category.

        Categories:
        - cs.AI: Artificial Intelligence
        - cs.CL: Computation and Language
        - cs.LG: Machine Learning
        - cs.CV: Computer Vision
        - stat.ML: Machine Learning (Statistics)
        """
        query = f"cat:{category}"
        return self.search(query, max_results)

    def get_paper_by_id(self, arxiv_id: str) -> ArxivPaper | None:
        """Get specific paper by arXiv ID (e.g., '2301.12345')."""
        self._rate_limit()

        url = f"{self.BASE_URL}?id_list={arxiv_id}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if feed.entries:
                return self._parse_entry(feed.entries[0])

            return None

        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None

    def download_pdf(
        self, paper: ArxivPaper, output_dir: str = "./papers"
    ) -> str | None:
        """
        Download PDF for a paper.

        Returns:
            Path to downloaded PDF or None if failed
        """
        self._rate_limit()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        filename = f"{paper.arxiv_id.replace('/', '_')}.pdf"
        filepath = output_path / filename

        try:
            response = requests.get(paper.pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded PDF: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error downloading PDF for {paper.arxiv_id}: {e}")
            return None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            with open(pdf_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)

                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                full_text = "\n\n".join(text_parts)

                # Clean up text
                full_text = self._clean_text(full_text)

                logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
                return full_text

        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

    def download_and_extract(
        self, paper: ArxivPaper, output_dir: str = "./papers"
    ) -> str | None:
        """
        Download PDF and extract text in one step.

        Returns:
            Extracted text or None if failed
        """
        pdf_path = self.download_pdf(paper, output_dir)

        if not pdf_path:
            return None

        text = self.extract_text_from_pdf(pdf_path)
        return text if text else None

    def _parse_entry(self, entry) -> ArxivPaper | None:
        """Parse feedparser entry into ArxivPaper."""
        try:
            # Extract arXiv ID from the id field
            arxiv_id = entry.id.split("/abs/")[-1]

            # Get authors
            authors = [author.name for author in entry.authors]

            # Get categories
            categories = [tag.term for tag in entry.tags]

            # PDF URL
            pdf_url = entry.id.replace("/abs/", "/pdf/") + ".pdf"

            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=entry.title,
                authors=authors,
                abstract=entry.summary,
                categories=categories,
                published=entry.published,
                pdf_url=pdf_url,
                arxiv_url=entry.id,
            )

        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove page numbers (simple heuristic)
        text = re.sub(r"\n\d+\n", "\n", text)

        # Remove common PDF artifacts
        text = text.replace("ﬁ", "fi")
        text = text.replace("ﬂ", "fl")
        text = text.replace("–", "-")
        text = text.replace(r"\’", "'")

        return text.strip()

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
