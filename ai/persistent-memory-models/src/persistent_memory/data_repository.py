"""
Centralized Data Repository for Research Papers.

Provides unified interface for downloading, caching, and accessing research papers.
Prevents duplicate downloads and provides efficient storage.
"""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from persistent_memory.arxiv_downloader import ArxivDownloader, ArxivPaper

logger = logging.getLogger(__name__)


class DataRepository:
    """
    Centralized repository for managing research paper data.
    
    Features:
    - Automatic caching (no re-downloads)
    - Metadata tracking
    - Deduplication
    - Efficient storage
    - Version tracking
    
    Directory structure:
        data/
        ├── papers/
        │   ├── 1706.03762/
        │   │   ├── metadata.json
        │   │   ├── paper.pdf
        │   │   └── extracted_text.txt
        │   └── 1409.0473/
        │       └── ...
        ├── cache/
        │   └── index.json
        └── processed/
            └── embeddings/
    """
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.papers_dir = self.base_dir / "papers"
        self.cache_dir = self.base_dir / "cache"
        self.processed_dir = self.base_dir / "processed"
        
        # Create directories
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load index
        self.index_path = self.cache_dir / "index.json"
        self.index = self._load_index()
        
        # Initialize downloader
        self.downloader = ArxivDownloader()
        
        logger.info(f"Initialized DataRepository at {self.base_dir}")
    
    def get_paper(
        self,
        arxiv_id: str,
        force_download: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get paper data (downloads if not cached).
        
        Args:
            arxiv_id: arXiv ID (e.g., '1706.03762')
            force_download: Force re-download even if cached
            
        Returns:
            Dictionary with paper data and paths
        """
        # Check cache first
        if not force_download and arxiv_id in self.index:
            logger.info(f"Paper {arxiv_id} found in cache")
            return self._load_cached_paper(arxiv_id)
        
        # Download paper
        logger.info(f"Downloading paper {arxiv_id}...")
        paper_data = self._download_and_store(arxiv_id)
        
        if paper_data:
            # Update index
            self.index[arxiv_id] = {
                'downloaded_at': datetime.now().isoformat(),
                'title': paper_data['metadata']['title'],
                'status': 'ready'
            }
            self._save_index()
        
        return paper_data
    
    def get_papers_batch(
        self,
        arxiv_ids: List[str],
        force_download: bool = False
    ) -> List[Dict[str, Any]]:
        """Get multiple papers efficiently."""
        papers = []
        
        for arxiv_id in arxiv_ids:
            paper = self.get_paper(arxiv_id, force_download)
            if paper:
                papers.append(paper)
        
        return papers
    
    def search_and_cache(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv and cache results.
        
        Returns list of paper data with local paths.
        """
        # Search arXiv
        papers = self.downloader.search(query, max_results=max_results)
        
        # Download and cache each
        cached_papers = []
        for paper in papers:
            paper_data = self.get_paper(paper.arxiv_id)
            if paper_data:
                cached_papers.append(paper_data)
        
        return cached_papers
    
    def get_text(self, arxiv_id: str) -> Optional[str]:
        """Get extracted text for a paper."""
        paper_dir = self.papers_dir / self._sanitize_id(arxiv_id)
        text_file = paper_dir / "extracted_text.txt"
        
        if text_file.exists():
            return text_file.read_text(encoding='utf-8')
        
        # Try to get paper (will download if needed)
        paper_data = self.get_paper(arxiv_id)
        if paper_data and 'text_path' in paper_data:
            return Path(paper_data['text_path']).read_text(encoding='utf-8')
        
        return None
    
    def get_pdf_path(self, arxiv_id: str) -> Optional[str]:
        """Get path to PDF file."""
        paper_dir = self.papers_dir / self._sanitize_id(arxiv_id)
        pdf_file = paper_dir / "paper.pdf"
        
        if pdf_file.exists():
            return str(pdf_file)
        
        # Download if needed
        paper_data = self.get_paper(arxiv_id)
        if paper_data and 'pdf_path' in paper_data:
            return paper_data['pdf_path']
        
        return None
    
    def is_cached(self, arxiv_id: str) -> bool:
        """Check if paper is already cached."""
        return arxiv_id in self.index
    
    def get_cached_papers(self) -> List[str]:
        """Get list of all cached paper IDs."""
        return list(self.index.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        total_papers = len(self.index)
        total_size = sum(
            self._get_dir_size(self.papers_dir / self._sanitize_id(arxiv_id))
            for arxiv_id in self.index.keys()
        )
        
        return {
            'total_papers': total_papers,
            'total_size_mb': total_size / (1024 * 1024),
            'papers': list(self.index.keys()),
            'base_dir': str(self.base_dir)
        }
    
    def clear_cache(self, arxiv_id: Optional[str] = None):
        """Clear cache for specific paper or all papers."""
        if arxiv_id:
            # Clear specific paper
            paper_dir = self.papers_dir / self._sanitize_id(arxiv_id)
            if paper_dir.exists():
                shutil.rmtree(paper_dir)
            
            if arxiv_id in self.index:
                del self.index[arxiv_id]
                self._save_index()
            
            logger.info(f"Cleared cache for {arxiv_id}")
        else:
            # Clear all
            shutil.rmtree(self.papers_dir)
            self.papers_dir.mkdir(parents=True, exist_ok=True)
            self.index = {}
            self._save_index()
            
            logger.info("Cleared entire cache")
    
    def _download_and_store(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Download paper and store in repository."""
        # Fetch metadata
        paper = self.downloader.get_paper_by_id(arxiv_id)
        
        if not paper:
            logger.error(f"Could not fetch metadata for {arxiv_id}")
            return None
        
        # Create paper directory
        paper_dir = self.papers_dir / self._sanitize_id(arxiv_id)
        paper_dir.mkdir(parents=True, exist_ok=True)
        
        # Download PDF
        pdf_path = self.downloader.download_pdf(paper, output_dir=str(paper_dir))
        
        if not pdf_path:
            logger.error(f"Could not download PDF for {arxiv_id}")
            return None
        
        # Rename to standard name
        standard_pdf_path = paper_dir / "paper.pdf"
        if Path(pdf_path) != standard_pdf_path:
            Path(pdf_path).rename(standard_pdf_path)
            pdf_path = str(standard_pdf_path)
        
        # Extract text
        text = self.downloader.extract_text_from_pdf(pdf_path)
        
        # Save extracted text
        text_path = paper_dir / "extracted_text.txt"
        text_path.write_text(text, encoding='utf-8')
        
        # Save metadata
        metadata = paper.to_dict()
        metadata['downloaded_at'] = datetime.now().isoformat()
        metadata['text_length'] = len(text)
        
        metadata_path = paper_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        
        logger.info(f"Stored paper {arxiv_id} in repository")
        
        return {
            'arxiv_id': arxiv_id,
            'metadata': metadata,
            'pdf_path': str(pdf_path),
            'text_path': str(text_path),
            'text': text,
            'paper_dir': str(paper_dir)
        }
    
    def _load_cached_paper(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Load paper data from cache."""
        paper_dir = self.papers_dir / self._sanitize_id(arxiv_id)
        
        if not paper_dir.exists():
            logger.warning(f"Paper directory not found for {arxiv_id}")
            return None
        
        # Load metadata
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            logger.warning(f"Metadata not found for {arxiv_id}")
            return None
        
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        
        # Get paths
        pdf_path = paper_dir / "paper.pdf"
        text_path = paper_dir / "extracted_text.txt"
        
        # Load text if available
        text = None
        if text_path.exists():
            text = text_path.read_text(encoding='utf-8')
        
        return {
            'arxiv_id': arxiv_id,
            'metadata': metadata,
            'pdf_path': str(pdf_path) if pdf_path.exists() else None,
            'text_path': str(text_path) if text_path.exists() else None,
            'text': text,
            'paper_dir': str(paper_dir)
        }
    
    def _load_index(self) -> Dict[str, Any]:
        """Load index from disk."""
        if self.index_path.exists():
            return json.loads(self.index_path.read_text(encoding='utf-8'))
        return {}
    
    def _save_index(self):
        """Save index to disk."""
        self.index_path.write_text(
            json.dumps(self.index, indent=2),
            encoding='utf-8'
        )
    
    def _sanitize_id(self, arxiv_id: str) -> str:
        """Sanitize arXiv ID for use as directory name."""
        return arxiv_id.replace('/', '_').replace(':', '_')
    
    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory in bytes."""
        if not path.exists():
            return 0
        
        total = 0
        for item in path.rglob('*'):
            if item.is_file():
                total += item.stat().st_size
        return total


# Global repository instance
_repository = None

def get_repository(base_dir: str = "./data") -> DataRepository:
    """Get global repository instance (singleton)."""
    global _repository
    if _repository is None:
        _repository = DataRepository(base_dir)
    return _repository


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    repo = DataRepository()
    
    # Get a paper (will download if not cached)
    print("Getting paper 1706.03762 (Attention Is All You Need)...")
    paper = repo.get_paper('1706.03762')
    
    if paper:
        print(f"\n✅ Paper retrieved!")
        print(f"   Title: {paper['metadata']['title']}")
        print(f"   PDF: {paper['pdf_path']}")
        print(f"   Text length: {len(paper['text'])} chars")
        print(f"   Cached: {repo.is_cached('1706.03762')}")
    
    # Get it again (should be instant from cache)
    print("\n\nGetting same paper again (from cache)...")
    paper2 = repo.get_paper('1706.03762')
    
    # Stats
    print("\n\nRepository stats:")
    stats = repo.get_stats()
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
    print(f"   Papers: {stats['papers']}")
