import asyncio
import logging
from scrapers import kitmondo_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_kitmondo():
    print("\n--- Testing Kitmondo (Selenium) ---")
    try:
        listings = await kitmondo_scraper.scrape()
        print(f"Kitmondo Results: {len(listings)} listings found")
        if listings:
            print(f"Sample: {listings[0].get('title')} | Price: {listings[0].get('current_price')}")
            # Print a few more titles to prove it's finding real stuff
            print("Top 5 Listings:")
            for l in listings[:5]:
                print(f"- {l.get('title')}")
    except Exception as e:
        print(f"Kitmondo Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kitmondo())
