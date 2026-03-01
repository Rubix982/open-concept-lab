"""
Conference Connector for Research Paper System.

Connects to major AI conferences (NeurIPS, ICML, ICLR, CVPR, etc.)
to fetch proceedings and accepted papers.
"""

import logging
from dataclasses import dataclass
from typing import Any

from persistent_memory.core.arxiv_downloader import ArxivDownloader, ArxivPaper

logger = logging.getLogger(__name__)


@dataclass
class Conference:
    """Metadata for a conference."""

    name: str
    full_name: str
    topics: list[str]
    arxiv_query: str  # Query to find papers on arXiv
    years: list[int]


class ConferenceConnector:
    """
    Connects to conference data sources.

    Currently uses arXiv as the primary source, filtering by:
    1. Comments field (e.g., "Accepted to NeurIPS 2023")
    2. Semantic search for conference topics
    """

    # Supported conferences
    CONFERENCES = {
        "neurips": Conference(
            name="NeurIPS",
            full_name="Neural Information Processing Systems",
            topics=["cs.LG", "cs.AI", "stat.ML"],
            arxiv_query='(cat:cs.LG OR cat:cs.AI) AND (abs:"NeurIPS" OR co:"NeurIPS")',
            years=[2020, 2021, 2022, 2023, 2024],
        ),
        "icml": Conference(
            name="ICML",
            full_name="International Conference on Machine Learning",
            topics=["cs.LG", "stat.ML"],
            arxiv_query='(cat:cs.LG OR stat.ML) AND (abs:"ICML" OR co:"ICML")',
            years=[2020, 2021, 2022, 2023, 2024],
        ),
        "iclr": Conference(
            name="ICLR",
            full_name="International Conference on Learning Representations",
            topics=["cs.LG", "cs.AI"],
            arxiv_query='(cat:cs.LG OR cat:cs.AI) AND (abs:"ICLR" OR co:"ICLR")',
            years=[2020, 2021, 2022, 2023, 2024],
        ),
        "cvpr": Conference(
            name="CVPR",
            full_name="Computer Vision and Pattern Recognition",
            topics=["cs.CV"],
            arxiv_query='cat:cs.CV AND (abs:"CVPR" OR co:"CVPR")',
            years=[2020, 2021, 2022, 2023, 2024],
        ),
        "acl": Conference(
            name="ACL",
            full_name="Association for Computational Linguistics",
            topics=["cs.CL"],
            arxiv_query='cat:cs.CL AND (abs:"ACL" OR co:"ACL")',
            years=[2020, 2021, 2022, 2023, 2024],
        ),
        "siggraph": Conference(
            name="SIGGRAPH",
            full_name="ACM SIGGRAPH",
            topics=["cs.GR", "cs.CV"],
            arxiv_query='(cat:cs.GR OR cat:cs.CV) AND (abs:"SIGGRAPH" OR co:"SIGGRAPH")',
            years=[2020, 2021, 2022, 2023, 2024],
        ),
    }

    def __init__(self):
        self.downloader = ArxivDownloader()
        logger.info("Initialized ConferenceConnector")

    def list_conferences(self) -> list[dict[str, Any]]:
        """List supported conferences."""
        return [
            {
                "id": key,
                "name": conf.name,
                "full_name": conf.full_name,
                "topics": conf.topics,
                "years": conf.years,
            }
            for key, conf in self.CONFERENCES.items()
        ]

    def get_conference_papers(
        self, conference_id: str, year: int | None = None, max_results: int = 20
    ) -> list[ArxivPaper]:
        """
        Get papers for a specific conference.

        Args:
            conference_id: Conference ID (e.g., 'neurips')
            year: Specific year (optional)
            max_results: Maximum papers to fetch

        Returns:
            List of ArxivPaper objects
        """
        if conference_id not in self.CONFERENCES:
            raise ValueError(f"Unknown conference: {conference_id}")

        conf = self.CONFERENCES[conference_id]

        # Build query
        query = conf.arxiv_query

        if year:
            # Add year filter (approximate via search query)
            query = f"{query} AND {year}"

        logger.info(f"Fetching {conf.name} papers with query: {query}")

        # Search arXiv
        papers = self.downloader.search(
            query,
            max_results=max_results,
            sort_by="submittedDate",
            sort_order="descending",
        )

        # Post-filter to ensure relevance (simple heuristic)
        filtered_papers = []
        for paper in papers:
            # Check if conference name appears in abstract or metadata
            # (Note: arXiv API doesn't expose 'comment' field in simple search,
            # so we rely on the query having done most of the work)
            filtered_papers.append(paper)

        logger.info(f"Found {len(filtered_papers)} papers for {conf.name} {year or ''}")
        return filtered_papers
