import asyncio
import logging
from scrapers import machineseeker_scraper, exapro_scraper, kitmondo_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_scrapers():
    print("--- Testing Kitmondo ---")
    try:
        kit_result = await kitmondo_scraper.scrape()
        print(f"Kitmondo Results: {len(kit_result)} listings found")
        if kit_result:
            print(f"Sample: {kit_result[0]}")
    except Exception as e:
        print(f"Kitmondo Failed: {e}")

    print("--- Testing Machineseeker ---")
    try:
        ms_result = await machineseeker_scraper.scrape()
        print(f"Machineseeker Results: {len(ms_result)} listings found")
        if ms_result:
            print(f"Sample: {ms_result[0]}")
    except Exception as e:
        print(f"Machineseeker Failed: {e}")

    print("\n--- Testing Exapro ---")
    try:
        ex_result = await exapro_scraper.scrape()
        print(f"Exapro Results: {len(ex_result)} listings found")
        if ex_result:
            print(f"Sample: {ex_result[0]}")
    except Exception as e:
        print(f"Exapro Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
