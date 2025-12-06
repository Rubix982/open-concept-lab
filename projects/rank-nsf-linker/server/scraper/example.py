"""Example usage and testing of the scraper."""
import asyncio
import logging
from scraper import FacultyScraper
from database import db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_single_professor():
    """Test scraping a single professor."""
    scraper = FacultyScraper(max_depth=2, delay=1.0)
    
    # Example: Scrape a professor's homepage
    results = await scraper.scrape_professor(
        professor_name="Test Professor",
        homepage="https://example.edu/~professor"  # Replace with real URL
    )
    
    logger.info(f"Scraped {len(results)} pages")
    for result in results:
        logger.info(f"  - {result['url']} ({result['content_type']})")
        logger.info(f"    Title: {result.get('title', 'N/A')}")
        logger.info(f"    Content length: {len(result.get('text', ''))} chars")


async def scrape_from_database(limit=5):
    """Scrape professors from database."""
    # Connect to database
    await db.connect()
    
    try:
        # Get professors with homepages
        professors = await db.get_professors_with_homepages(limit=limit)
        logger.info(f"Found {len(professors)} professors with homepages")
        
        if not professors:
            logger.warning("No professors with homepages found")
            return
        
        # Scrape each professor
        scraper = FacultyScraper()
        
        for prof in professors:
            logger.info(f"\nScraping {prof['name']}...")
            results = await scraper.scrape_professor(
                professor_name=prof['name'],
                homepage=prof['homepage']
            )
            
            # Save to database
            if results:
                saved = await db.save_scraped_content(results)
                logger.info(f"Saved {saved} pages for {prof['name']}")
            
            # Small delay between professors
            await asyncio.sleep(2)
    
    finally:
        await db.close()


async def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode with example URL
        await test_single_professor()
    else:
        # Production mode: scrape from database
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
        await scrape_from_database(limit=limit)


if __name__ == '__main__':
    asyncio.run(main())
