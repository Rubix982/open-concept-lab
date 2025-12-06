"""Main scraper orchestrator."""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .crawler import WebCrawler
from .config import config
from .cache import scrape_cache

logger = logging.getLogger(__name__)


class FacultyScraper:
    """Main scraper for professor homepages."""
    
    def __init__(
        self,
        max_depth: int = None,
        delay: float = None,
        use_cache: bool = True
    ):
        self.max_depth = max_depth or config.max_depth
        self.delay = delay or config.delay_seconds
        self.use_cache = use_cache
        self.crawler = WebCrawler(
            max_depth=self.max_depth,
            delay=self.delay,
            timeout=config.timeout_seconds
        )
    
    async def scrape_professor(
        self,
        professor_name: str,
        homepage: str
    ) -> List[Dict]:
        """
        Scrape a professor's homepage and related pages.
        
        Args:
            professor_name: Name of the professor
            homepage: Professor's homepage URL
            
        Returns:
            List of scraped content dictionaries
        """
        # Check cache first
        if self.use_cache and scrape_cache.has_cached(professor_name):
            logger.info(f"Loading {professor_name} from cache")
            cached = scrape_cache.load_cached(professor_name)
            if cached:
                return cached
        
        logger.info(f"Starting scrape for {professor_name} at {homepage}")
        
        try:
            # Crawl the homepage
            results = await self.crawler.crawl(homepage)
            
            # Add professor metadata to each result
            for result in results:
                result['professor_name'] = professor_name
                result['professor_homepage'] = homepage
                result['scraped_at'] = datetime.utcnow().isoformat()
            
            # Save to cache
            if self.use_cache and results:
                scrape_cache.save_to_cache(professor_name, results)
            
            logger.info(f"Scraped {len(results)} pages for {professor_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error scraping {professor_name}: {e}")
            return []
    
    async def scrape_batch(
        self,
        professors: List[Dict[str, str]]
    ) -> Dict[str, List[Dict]]:
        """
        Scrape multiple professors concurrently.
        
        Args:
            professors: List of dicts with 'name' and 'homepage' keys
            
        Returns:
            Dict mapping professor names to their scraped content
        """
        tasks = [
            self.scrape_professor(prof['name'], prof['homepage'])
            for prof in professors
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dict
        output = {}
        for prof, result in zip(professors, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {prof['name']}: {result}")
                output[prof['name']] = []
            else:
                output[prof['name']] = result
        
        return output


# Convenience function for single professor
async def scrape_professor(name: str, homepage: str) -> List[Dict]:
    """Scrape a single professor's homepage."""
    scraper = FacultyScraper()
    return await scraper.scrape_professor(name, homepage)
