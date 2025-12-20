import asyncio
import logging
from scrapers import machineseeker_scraper, kitmondo_scraper, pressxchange_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_scrapers():
    print("--- Testing Machineseeker (Selenium) ---")
    try:
        ms_result = await machineseeker_scraper.scrape()
        print(f"Machineseeker Results: {len(ms_result)} listings found")
        if ms_result: print(f"Sample: {ms_result[0]['title']}")
    except Exception as e:
        print(f"Machineseeker Failed: {e}")

    print("\n--- Testing Kitmondo (Crawling) ---")
    try:
        kit_result = await kitmondo_scraper.scrape()
        print(f"Kitmondo Results: {len(kit_result)} listings found")
        if kit_result: print(f"Sample: {kit_result[0]['title']}")
    except Exception as e:
        print(f"Kitmondo Failed: {e}")

    print("\n--- Testing PressXchange (New) ---")
    try:
        px_result = await pressxchange_scraper.scrape()
        print(f"PressXchange Results: {len(px_result)} listings found")
        if px_result: print(f"Sample: {px_result[0]['title']}")
    except Exception as e:
        print(f"PressXchange Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
