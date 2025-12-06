"""Orchestrator for embedding generation and Qdrant ingestion."""
import asyncio
import asyncpg
from typing import List, Dict
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embeddings.embedder import ResearchEmbedder
from embeddings.config import config as embedding_config
from qdrant.client import qdrant_service
from qdrant.config import config as qdrant_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Pipeline for generating embeddings and ingesting to Qdrant."""
    
    def __init__(self):
        self.embedder = ResearchEmbedder()
        self.qdrant = qdrant_service
        self.db_pool = None
    
    async def connect_db(self):
        """Connect to PostgreSQL."""
        self.db_pool = await asyncpg.create_pool(
            embedding_config.postgres_dsn,
            min_size=2,
            max_size=10
        )
        logger.info("Connected to PostgreSQL")
    
    async def close_db(self):
        """Close database connection."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Closed PostgreSQL connection")
    
    async def get_unprocessed_content(self, limit: int = None) -> List[Dict]:
        """Get scraped content that hasn't been embedded yet."""
        query = """
            SELECT id, professor_name, url, content_type, title, content
            FROM scraped_content
            WHERE embedding_generated = FALSE
            ORDER BY scraped_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    async def mark_as_embedded(self, content_ids: List[str]):
        """Mark content as having embeddings generated."""
        query = """
            UPDATE scraped_content
            SET embedding_generated = TRUE
            WHERE id = ANY($1)
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, content_ids)
    
    def prepare_metadata(self, content: Dict) -> Dict:
        """Prepare metadata for Qdrant."""
        return {
            'professor_name': content['professor_name'],
            'url': content['url'],
            'content_type': content.get('content_type', 'homepage'),
            'title': content.get('title', ''),
            'content_snippet': content.get('content', '')[:200]  # First 200 chars
        }
    
    async def process_batch(self, batch_size: int = 100) -> int:
        """
        Process a batch of unprocessed content.
        
        Returns:
            Number of embeddings generated
        """
        # Get unprocessed content
        content_list = await self.get_unprocessed_content(limit=batch_size)
        
        if not content_list:
            logger.info("No unprocessed content found")
            return 0
        
        logger.info(f"Processing {len(content_list)} content items...")
        
        # Generate embeddings
        embeddings = self.embedder.embed_content_batch(content_list)
        
        # Prepare metadata
        metadata_list = [self.prepare_metadata(c) for c in content_list]
        
        # Ingest to Qdrant
        count = self.qdrant.ingest_batch(embeddings, metadata_list)
        
        # Mark as embedded in database
        content_ids = [str(c['id']) for c in content_list]
        await self.mark_as_embedded(content_ids)
        
        logger.info(f"Successfully processed {count} embeddings")
        return count
    
    async def process_all(self, batch_size: int = 100):
        """Process all unprocessed content in batches."""
        total_processed = 0
        
        while True:
            count = await self.process_batch(batch_size)
            if count == 0:
                break
            total_processed += count
            logger.info(f"Total processed so far: {total_processed}")
        
        logger.info(f"Finished processing. Total: {total_processed} embeddings")
        return total_processed


async def main():
    """Main entry point."""
    import sys
    
    # Parse arguments
    batch_size = 100
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    
    pipeline = EmbeddingPipeline()
    
    try:
        # Connect to database
        await pipeline.connect_db()
        
        # Create Qdrant collection if needed
        pipeline.qdrant.create_collection(vector_size=pipeline.embedder.dimension)
        
        # Process all content
        total = await pipeline.process_all(batch_size=batch_size)
        
        # Show collection info
        info = pipeline.qdrant.get_collection_info()
        logger.info(f"Qdrant collection info: {info}")
        
    finally:
        await pipeline.close_db()


if __name__ == '__main__':
    asyncio.run(main())
