"""Configuration for the scraper service."""
import os
from dataclasses import dataclass

@dataclass
class ScraperConfig:
    """Scraper configuration."""
    
    # Crawling settings
    max_depth: int = int(os.getenv('SCRAPER_MAX_DEPTH', '2'))
    delay_seconds: float = float(os.getenv('SCRAPER_DELAY', '1.0'))
    timeout_seconds: int = int(os.getenv('SCRAPER_TIMEOUT', '10'))
    max_retries: int = int(os.getenv('SCRAPER_MAX_RETRIES', '3'))
    
    # Content settings
    max_content_length: int = int(os.getenv('SCRAPER_MAX_CONTENT', '50000'))  # 50KB
    follow_external_links: bool = os.getenv('SCRAPER_FOLLOW_EXTERNAL', 'false').lower() == 'true'
    
    # Database settings
    postgres_host: str = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port: int = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user: str = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password: str = os.getenv('POSTGRES_PASSWORD', '')
    postgres_db: str = os.getenv('POSTGRES_DB_NAME', 'rank_nsf_linker')
    
    # User agent
    user_agent: str = os.getenv(
        'SCRAPER_USER_AGENT',
        'FacultyResearchBot/1.0 (+https://github.com/yourorg/faculty-scraper)'
    )
    
    @property
    def postgres_dsn(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


config = ScraperConfig()
