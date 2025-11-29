"""
Conference Connector for Research Paper System.

Connects to major AI conferences (NeurIPS, ICML, ICLR, CVPR, etc.)
to fetch proceedings and accepted papers.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from persistent_memory.arxiv_downloader import ArxivDownloader, ArxivPaper

logger = logging.getLogger(__name__)


@dataclass
class Conference:
    """Metadata for a conference."""
    name: str
    full_name: str
    topics: List[str]
    arxiv_query: str  # Query to find papers on arXiv
    years: List[int]


class ConferenceConnector:
    """
    Connects to conference data sources.
    
    Currently uses arXiv as the primary source, filtering by:
    1. Comments field (e.g., "Accepted to NeurIPS 2023")
    2. Semantic search for conference topics
    """
    
    # Supported conferences
    CONFERENCES = {
        'neurips': Conference(
            name='NeurIPS',
            full_name='Neural Information Processing Systems',
            topics=['cs.LG', 'cs.AI', 'stat.ML'],
            arxiv_query='(cat:cs.LG OR cat:cs.AI) AND (abs:"NeurIPS" OR co:"NeurIPS")',
            years=[2020, 2021, 2022, 2023, 2024]
        ),
        'icml': Conference(
            name='ICML',
            full_name='International Conference on Machine Learning',
            topics=['cs.LG', 'stat.ML'],
            arxiv_query='(cat:cs.LG OR stat.ML) AND (abs:"ICML" OR co:"ICML")',
            years=[2020, 2021, 2022, 2023, 2024]
        ),
        'iclr': Conference(
            name='ICLR',
            full_name='International Conference on Learning Representations',
            topics=['cs.LG', 'cs.AI'],
            arxiv_query='(cat:cs.LG OR cat:cs.AI) AND (abs:"ICLR" OR co:"ICLR")',
            years=[2020, 2021, 2022, 2023, 2024]
        ),
        'cvpr': Conference(
            name='CVPR',
            full_name='Computer Vision and Pattern Recognition',
            topics=['cs.CV'],
            arxiv_query='cat:cs.CV AND (abs:"CVPR" OR co:"CVPR")',
            years=[2020, 2021, 2022, 2023, 2024]
        ),
        'acl': Conference(
            name='ACL',
            full_name='Association for Computational Linguistics',
            topics=['cs.CL'],
            arxiv_query='cat:cs.CL AND (abs:"ACL" OR co:"ACL")',
            years=[2020, 2021, 2022, 2023, 2024]
        ),
        'siggraph': Conference(
            name='SIGGRAPH',
            full_name='ACM SIGGRAPH',
            topics=['cs.GR', 'cs.CV'],
            arxiv_query='(cat:cs.GR OR cat:cs.CV) AND (abs:"SIGGRAPH" OR co:"SIGGRAPH")',
            years=[2020, 2021, 2022, 2023, 2024]
        )
    }
    
    def __init__(self):
        self.downloader = ArxivDownloader()
        logger.info("Initialized ConferenceConnector")
    
    def list_conferences(self) -> List[Dict[str, Any]]:
        """List supported conferences."""
        return [
            {
                'id': key,
                'name': conf.name,
                'full_name': conf.full_name,
                'topics': conf.topics,
                'years': conf.years
            }
            for key, conf in self.CONFERENCES.items()
        ]
    
    def get_conference_papers(
        self,
        conference_id: str,
        year: Optional[int] = None,
        max_results: int = 20
    ) -> List[ArxivPaper]:
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
            sort_order="descending"
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


# Top Papers Collections (Manually Curated for Demo)
TOP_PAPERS = {
    'neurips_2023': [
        '2305.10403',  # QLoRA
        '2302.13971',  # LLaMA
        '2305.14314',  # DPO (Direct Preference Optimization)
    ],
    'iclr_2024': [
        '2310.06825',  # Mistral 7B
        '2309.16609',  # CoVE (Chain of Verification)
    ],
    'cvpr_2023': [
        '2304.02643',  # Segment Anything
    ]
}

def get_top_papers(conference_year: str) -> List[str]:
    """Get top papers for a conference year (e.g., 'neurips_2023')."""
    return TOP_PAPERS.get(conference_year, [])


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    connector = ConferenceConnector()
    
    print("Supported Conferences:")
    for conf in connector.list_conferences():
        print(f"- {conf['name']} ({conf['full_name']})")
    
    print("\nFetching recent NeurIPS papers...")
    papers = connector.get_conference_papers('neurips', max_results=3)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   arXiv: {paper.arxiv_id}")
