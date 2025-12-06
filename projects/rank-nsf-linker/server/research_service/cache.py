"""Cache manager for scraped content."""
import os
import json
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ScrapeCache:
    """Manages caching of scraped content to disk."""
    
    def __init__(self, cache_dir: str = "/app/data/scraped_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Scrape cache directory: {self.cache_dir}")
    
    def _get_cache_file(self, professor_name: str) -> Path:
        """Get cache file path for a professor."""
        # Sanitize filename
        safe_name = professor_name.replace("/", "_").replace(" ", "_")
        return self.cache_dir / f"{safe_name}.json"
    
    def has_cached(self, professor_name: str) -> bool:
        """Check if professor's content is cached."""
        cache_file = self._get_cache_file(professor_name)
        exists = cache_file.exists()
        if exists:
            logger.info(f"✓ Cache hit for {professor_name}")
        return exists
    
    def load_cached(self, professor_name: str) -> Optional[List[Dict]]:
        """Load cached content for a professor."""
        cache_file = self._get_cache_file(professor_name)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} cached pages for {professor_name}")
                return data
        except Exception as e:
            logger.error(f"Error loading cache for {professor_name}: {e}")
            return None
    
    def save_to_cache(self, professor_name: str, content: List[Dict]):
        """Save scraped content to cache."""
        cache_file = self._get_cache_file(professor_name)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(content, f, indent=2)
            logger.info(f"Cached {len(content)} pages for {professor_name}")
        except Exception as e:
            logger.error(f"Error saving cache for {professor_name}: {e}")
    
    def clear_cache(self, professor_name: Optional[str] = None):
        """Clear cache for a professor or all cache."""
        if professor_name:
            cache_file = self._get_cache_file(professor_name)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for {professor_name}")
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared all cache")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'cached_professors': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# Global cache instance
scrape_cache = ScrapeCache()
