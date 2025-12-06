# Faculty Research Scraper

Web scraping service for extracting research content from professor homepages.

## Structure

```
scraper/
├── __init__.py
├── scraper.py          # Main scraper orchestrator
├── crawler.py          # Recursive web crawler
├── extractors.py       # Content extraction
├── cleaners.py         # Text cleaning
├── queue_manager.py    # Scrape queue management
├── config.py           # Configuration
├── requirements.txt    # Python dependencies
└── Dockerfile         # Container definition
```

## Features

- Recursive crawling (configurable depth)
- Content extraction from HTML and PDF
- Rate limiting and robots.txt compliance
- Error handling and retry logic
- PostgreSQL integration for queue and storage

## Usage

```python
from scraper import FacultyScraper

scraper = FacultyScraper(max_depth=2, delay=1.0)
results = await scraper.scrape_professor("John Doe", "https://example.edu/~jdoe")
```
