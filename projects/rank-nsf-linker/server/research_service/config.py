"""Configuration for Qdrant service."""
import os
from dataclasses import dataclass

@dataclass
class QdrantConfig:
    """Qdrant service configuration."""
    
    # Qdrant settings
    host: str = os.getenv('QDRANT_HOST', 'qdrant-local')
    port: int = int(os.getenv('QDRANT_PORT', '6333'))
    collection_name: str = os.getenv('QDRANT_COLLECTION', 'faculty_research')
    
    # Vector settings
    vector_size: int = int(os.getenv('VECTOR_SIZE', '384'))  # all-MiniLM-L6-v2
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


config = QdrantConfig()
