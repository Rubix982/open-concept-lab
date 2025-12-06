"""Unified configuration for research service."""
import os
from dataclasses import dataclass


@dataclass
class ResearchServiceConfig:
    """Unified configuration for scraper, embeddings, and Qdrant."""
    
    # Scraper settings
    max_depth: int = int(os.getenv('SCRAPER_MAX_DEPTH', '2'))
    delay_seconds: float = float(os.getenv('SCRAPER_DELAY', '1.0'))
    timeout_seconds: int = int(os.getenv('SCRAPER_TIMEOUT', '10'))
    max_retries: int = int(os.getenv('SCRAPER_MAX_RETRIES', '3'))
    max_content_length: int = int(os.getenv('SCRAPER_MAX_CONTENT', '50000'))
    follow_external_links: bool = os.getenv('SCRAPER_FOLLOW_EXTERNAL', 'false').lower() == 'true'
    user_agent: str = os.getenv(
        'SCRAPER_USER_AGENT',
        'FacultyResearchBot/1.0 (+https://github.com/yourorg/faculty-scraper)'
    )
    
    # Embedding settings
    model_name: str = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    batch_size: int = int(os.getenv('EMBEDDING_BATCH_SIZE', '32'))
    max_seq_length: int = int(os.getenv('EMBEDDING_MAX_LENGTH', '512'))
    
    # Qdrant settings
    qdrant_host: str = os.getenv('QDRANT_HOST', 'qdrant-local')
    qdrant_port: int = int(os.getenv('QDRANT_PORT', '6333'))
    collection_name: str = os.getenv('QDRANT_COLLECTION', 'faculty_research')
    vector_size: int = int(os.getenv('VECTOR_SIZE', '384'))
    distance_metric: str = os.getenv('DISTANCE_METRIC', 'Cosine')
    
    # Database settings
    postgres_host: str = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port: int = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user: str = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password: str = os.getenv('POSTGRES_PASSWORD', '')
    postgres_db: str = os.getenv('POSTGRES_DB_NAME', 'rank_nsf_linker')
    
    @property
    def postgres_dsn(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def vector_dimension(self) -> int:
        """Get vector dimension based on model."""
        dimensions = {
            'all-MiniLM-L6-v2': 384,
            'all-mpnet-base-v2': 768,
            'all-MiniLM-L12-v2': 384,
        }
        return dimensions.get(self.model_name, 384)


config = ResearchServiceConfig()
