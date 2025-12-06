# Research Service

Unified service for faculty research content processing: scraping, embedding generation, and semantic search.

## Structure

```
research_service/
├── scraper.py          # Web scraping
├── crawler.py          # Recursive crawler
├── extractors.py       # Content extraction
├── embedder.py         # Embedding generation
├── client.py           # Qdrant client
├── pipeline.py         # Orchestration
├── search_api.py       # Search endpoint
├── database.py         # PostgreSQL integration
├── config.py           # Configuration
├── example.py          # Usage examples
└── requirements.txt    # Dependencies
```

## Features

### 1. Web Scraping
- Recursive crawling of professor homepages
- Content extraction and cleaning
- Rate limiting and robots.txt compliance

### 2. Embedding Generation
- sentence-transformers (all-MiniLM-L6-v2)
- Batch processing
- 384-dimensional vectors

### 3. Vector Storage
- Qdrant integration
- Semantic search
- Metadata indexing

## Usage

### Scrape Homepages
```bash
python example.py 100  # Scrape 100 professors
```

### Generate Embeddings
```bash
python pipeline.py 100  # Process 100 items
```

### Search
```bash
python search_api.py < query.json
```

## Environment Variables

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB_NAME=rank_nsf_linker

# Qdrant
QDRANT_HOST=qdrant-local
QDRANT_PORT=6333

# Scraper
SCRAPER_MAX_DEPTH=2
SCRAPER_DELAY=1.0

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32
```
