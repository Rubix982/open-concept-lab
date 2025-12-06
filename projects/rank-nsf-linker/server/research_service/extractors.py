"""Content extraction from web pages."""
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
import trafilatura


class ContentExtractor:
    """Extract clean content from HTML."""
    
    def __init__(self, max_length: int = 50000):
        self.max_length = max_length
    
    def extract_from_html(self, html: str, url: str) -> Dict[str, str]:
        """Extract title and clean text from HTML."""
        # Use trafilatura for main content
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            include_images=False,
            no_fallback=False
        )
        
        if not text:
            # Fallback to BeautifulSoup
            text = self._fallback_extraction(html)
        
        # Extract title
        soup = BeautifulSoup(html, 'html.parser')
        title = ''
        if soup.find('title'):
            title = soup.find('title').get_text(strip=True)
        elif soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        
        # Clean and truncate
        text = self._clean_text(text or '')
        
        return {
            'title': title[:500],  # Limit title length
            'text': text[:self.max_length],
            'url': url
        }
    
    def _fallback_extraction(self, html: str) -> str:
        """Fallback extraction using BeautifulSoup."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        return text
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        return text.strip()
    
    def classify_content_type(self, url: str, title: str = '') -> str:
        """Classify content type based on URL and title."""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Check URL patterns
        if any(keyword in url_lower for keyword in ['publication', 'paper', 'pub']):
            return 'publication'
        elif any(keyword in url_lower for keyword in ['project', 'research']):
            return 'project'
        elif any(keyword in url_lower for keyword in ['bio', 'about', 'cv', 'resume']):
            return 'bio'
        elif any(keyword in url_lower for keyword in ['teaching', 'course']):
            return 'teaching'
        
        # Check title patterns
        if any(keyword in title_lower for keyword in ['publications', 'papers']):
            return 'publication'
        elif any(keyword in title_lower for keyword in ['research', 'projects']):
            return 'project'
        
        return 'homepage'
