"""Package initialization."""
from .scraper import FacultyScraper, scrape_professor
from .config import config

__all__ = ['FacultyScraper', 'scrape_professor', 'config']
