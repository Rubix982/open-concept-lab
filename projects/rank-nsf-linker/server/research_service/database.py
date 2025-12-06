"""Database integration for scraper."""
import asyncpg
from typing import List, Dict, Optional
import logging

from .config import config

logger = logging.getLogger(__name__)


class ScraperDB:
    """Database operations for scraper."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool."""
        self.pool = await asyncpg.create_pool(
            config.postgres_dsn,
            min_size=2,
            max_size=10
        )
        logger.info("Connected to PostgreSQL")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Closed PostgreSQL connection")
    
    async def get_professors_with_homepages(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get professors who have homepages."""
        query = """
            SELECT name, homepage, affiliation
            FROM professors
            WHERE homepage IS NOT NULL AND homepage != ''
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    async def save_scraped_content(
        self,
        content_list: List[Dict]
    ) -> int:
        """
        Save scraped content to database.
        
        Returns:
            Number of rows inserted
        """
        if not content_list:
            return 0
        
        query = """
            INSERT INTO scraped_content (
                professor_name, url, content_type, title, content, scraped_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (professor_name, url) 
            DO UPDATE SET
                content = EXCLUDED.content,
                last_updated = NOW()
        """
        
        async with self.pool.acquire() as conn:
            count = 0
            for content in content_list:
                try:
                    await conn.execute(
                        query,
                        content['professor_name'],
                        content['url'],
                        content.get('content_type', 'homepage'),
                        content.get('title', ''),
                        content.get('text', ''),
                        content.get('scraped_at')
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error saving content for {content.get('url')}: {e}")
            
            return count
    
    async def get_unprocessed_content(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get scraped content that hasn't been embedded yet."""
        query = """
            SELECT id, professor_name, url, content_type, title, content
            FROM scraped_content
            WHERE embedding_generated = FALSE
            ORDER BY scraped_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    async def mark_as_embedded(self, content_ids: List[str]):
        """Mark content as having embeddings generated."""
        query = """
            UPDATE scraped_content
            SET embedding_generated = TRUE
            WHERE id = ANY($1)
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, content_ids)


# Global instance
db = ScraperDB()
