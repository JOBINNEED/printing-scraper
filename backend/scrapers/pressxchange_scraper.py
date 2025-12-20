import asyncio
from bs4 import BeautifulSoup
import logging
from typing import List
import hashlib
from .common import extract_manufacturer, extract_model
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random
import time

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pressxchange.com"

# Search URLs
SEARCH_URLS = [
    "/en/search/searchterm/offset/",
    "/en/search/searchterm/packaging/",
    "/en/search/searchterm/spare+parts/"
]

def get_driver():
    options = Options()
    # Try headless first; user can disable if blocked
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_category_sync(endpoint: str, category_name: str) -> List[dict]:
    listings = []
    driver = None
    try:
        url = f"{BASE_URL}{endpoint}"
        logger.info(f"PressXchange - Starting Selenium for {url}")
        driver = get_driver()
        driver.get(url)
        
        # Human-like delay
        time.sleep(random.uniform(3, 6))
        
        # Scroll nicely
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
        time.sleep(1)
        
        html = driver.page_source
        listings = parse_listings(html, category_name)
        
    except Exception as e:
        logger.error(f"PressXchange - Selenium error for {endpoint}: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    return listings

async def scrape() -> List[dict]:
    all_listings = []
    loop = asyncio.get_running_loop()
    
    for endpoint in SEARCH_URLS:
        try:
            category = endpoint.split("q=")[-1].replace('+', ' ').title()
            
            # Run blocking Selenium code in a separate thread
            listings = await loop.run_in_executor(None, scrape_category_sync, endpoint, category)
            
            all_listings.extend(listings)
            logger.info(f"PressXchange - Found {len(listings)} listings for {category}")
            
        except Exception as e:
            logger.error(f"PressXchange - Error scraping {endpoint}: {e}")
            
    return all_listings

def parse_listings(html: str, category: str) -> List[dict]:
    listings = []
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Selectors confirmed by browser agent
        # Titles are in a tags with title starting with "Show details for"
        title_links = soup.select('a[title^="Show details for"]')
        
        logger.info(f"PressXchange - Parsing HTML... Found {len(title_links)} potential items")
        
        for link in title_links[:20]:
            try:
                title = link.get_text(strip=True)
                href = link['href']
                url = href if href.startswith('http') else BASE_URL + href
                
                # Container: usually a parent div of the link
                container = link.find_parent('div', class_='row') or link.find_parent('div')
                
                machine_id = hashlib.md5(url.encode()).hexdigest()
                
                price = None 
                currency = "EUR" 
                
                year = None
                if container:
                    text = container.get_text()
                    year_match = re.search(r'Year:\s*(\d{4})', text)
                    if year_match:
                        year = year_match.group(1)
                        
                listings.append({
                    "machine_id": machine_id,
                    "title": title,
                    "category": category,
                    "manufacturer": extract_manufacturer(title),
                    "model": extract_model(title),
                    "seller": "PressXchange Seller",
                    "source": "PressXchange",
                    "listing_url": url,
                    "current_price": price,
                    "currency": currency,
                    "year": year,
                    "location": None,
                    "status": "Active"
                })
            except Exception as e:
                continue
                
    except Exception as e:
        logger.error(f"Error parsing PressXchange HTML: {e}")
        
    return listings
