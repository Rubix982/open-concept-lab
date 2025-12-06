"""Package initialization for research service."""
from .scraper import FacultyScraper, scrape_professor
from .embedder import ResearchEmbedder
from .client import qdrant_service, QdrantService
from .config import config

__all__ = [
    'FacultyScraper',
    'scrape_professor',
    'ResearchEmbedder',
    'qdrant_service',
    'QdrantService',
    'config'
]
