"""Recursive web crawler for professor homepages."""
import asyncio
import aiohttp
from typing import List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse
from robotexclusionrulesparser import RobotExclusionRulesParser
import logging

from .config import config
from .extractors import ContentExtractor

logger = logging.getLogger(__name__)


class WebCrawler:
    """Recursive web crawler with politeness and rate limiting."""
    
    def __init__(
        self,
        max_depth: int = 2,
        delay: float = 1.0,
        timeout: int = 10
    ):
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.visited: Set[str] = set()
        self.extractor = ContentExtractor()
        self.robots_cache: dict = {}
    
    async def crawl(
        self,
        start_url: str,
        base_domain: Optional[str] = None
    ) -> List[dict]:
        """
        Crawl starting from start_url up to max_depth.
        
        Args:
            start_url: Starting URL to crawl
            base_domain: If provided, only crawl URLs from this domain
            
        Returns:
            List of extracted content dictionaries
        """
        if base_domain is None:
            base_domain = urlparse(start_url).netloc
        
        results = []
        queue: List[Tuple[str, int]] = [(start_url, 0)]  # (url, depth)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': config.user_agent}
        ) as session:
            while queue:
                url, depth = queue.pop(0)
                
                # Skip if already visited or max depth reached
                if url in self.visited or depth > self.max_depth:
                    continue
                
                # Check robots.txt
                if not await self._is_allowed(url):
                    logger.info(f"Skipping {url} (robots.txt)")
                    continue
                
                self.visited.add(url)
                logger.info(f"Crawling {url} (depth={depth})")
                
                # Fetch and extract content
                content = await self._fetch_and_extract(session, url)
                
                if content:
                    content['depth'] = depth
                    results.append(content)
                    
                    # Find and queue links if not at max depth
                    if depth < self.max_depth:
                        links = await self._extract_links(session, url, base_domain)
                        for link in links:
                            if link not in self.visited:
                                queue.append((link, depth + 1))
                
                # Rate limiting
                await asyncio.sleep(self.delay)
        
        return results
    
    async def _fetch_and_extract(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Optional[dict]:
        """Fetch URL and extract content."""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                # Only process HTML content
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type:
                    logger.info(f"Skipping non-HTML content: {url}")
                    return None
                
                html = await response.text()
                
                # Extract content
                extracted = self.extractor.extract_from_html(html, url)
                extracted['content_type'] = self.extractor.classify_content_type(
                    url,
                    extracted.get('title', '')
                )
                
                return extracted
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        
        return None
    
    async def _extract_links(
        self,
        session: aiohttp.ClientSession,
        url: str,
        base_domain: str
    ) -> List[str]:
        """Extract links from a page."""
        try:
            async with session.get(url) as response:
                html = await response.text()
                
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                
                # Parse URL
                parsed = urlparse(absolute_url)
                
                # Skip non-HTTP(S) links
                if parsed.scheme not in ['http', 'https']:
                    continue
                
                # Only follow links from same domain (unless configured otherwise)
                if not config.follow_external_links and parsed.netloc != base_domain:
                    continue
                
                # Skip common non-content URLs
                if self._should_skip_url(absolute_url):
                    continue
                
                links.append(absolute_url)
            
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return []
    
    def _should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped."""
        skip_extensions = [
            '.pdf', '.doc', '.docx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.jpg', '.png', '.gif',
            '.mp4', '.avi', '.mov'
        ]
        
        skip_patterns = [
            'mailto:', 'javascript:', 'tel:',
            '/login', '/logout', '/admin',
            '/calendar', '/events'
        ]
        
        url_lower = url.lower()
        
        # Check extensions
        if any(url_lower.endswith(ext) for ext in skip_extensions):
            return True
        
        # Check patterns
        if any(pattern in url_lower for pattern in skip_patterns):
            return True
        
        return False
    
    async def _is_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Check cache
        if base_url in self.robots_cache:
            parser = self.robots_cache[base_url]
        else:
            # Fetch and parse robots.txt
            parser = RobotExclusionRulesParser()
            robots_url = f"{base_url}/robots.txt"
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url, timeout=5) as response:
                        if response.status == 200:
                            robots_txt = await response.text()
                            parser.parse(robots_txt)
            except Exception:
                # If robots.txt fetch fails, assume allowed
                pass
            
            self.robots_cache[base_url] = parser
        
        return parser.is_allowed(config.user_agent, url)
