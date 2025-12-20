import asyncio
import logging
import aiohttp
from scrapers import machineseeker_scraper

async def debug_html():
    url = "https://www.machineseeker.com/offset-presses"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            html = await response.text()
            with open("debug_machineseeker.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Saved debug_machineseeker.html")

if __name__ == "__main__":
    asyncio.run(debug_html())
