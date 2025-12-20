import asyncio
from bs4 import BeautifulSoup
import logging
from typing import List
import hashlib
from .common import extract_manufacturer, extract_model

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random
import time

logger = logging.getLogger(__name__)

BASE_URL = "https://www.machineseeker.com"

# Categories to scrape
CATEGORIES = [
    "/Printing-machinery/ci-16",
]

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_category_sync(category_url: str, category_name: str) -> List[dict]:
    listings = []
    driver = None
    try:
        logger.info(f"Machineseeker - Starting Selenium for {category_url}")
        driver = get_driver()
        driver.get(category_url)
        
        # Human-like delay
        time.sleep(random.uniform(3, 6))
        
        # Scroll down to trigger lazy loading if any
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        
        html = driver.page_source
        listings = parse_listings(html, category_name)
        
    except Exception as e:
        logger.error(f"Machineseeker - Selenium error for {category_url}: {e}")
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
    
    for category_path in CATEGORIES:
        try:
            url = f"{BASE_URL}{category_path}"
            cat_name = category_path.split('/')[-1].replace('-', ' ').title()
            
            # Run blocking Selenium code in a separate thread
            listings = await loop.run_in_executor(None, scrape_category_sync, url, cat_name)
            
            all_listings.extend(listings)
            logger.info(f"Machineseeker - Found {len(listings)} listings in {cat_name}")
            
        except Exception as e:
            logger.error(f"Machineseeker - Error scraping {category_path}: {e}")
            
    if len(all_listings) == 0:
        logger.warning("Machineseeker scraper returned 0 results even with Selenium!")
        
    return all_listings

def parse_listings(html: str, category: str) -> List[dict]:
    listings = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Verified selector from browser agent
        items = soup.select('section.grid-card')
        
        logger.info(f"Machineseeker - Parsing HTML... Found {len(items)} potential items")
        
        for item in items[:20]:
            try:
                # Title - h2 tag inside the card
                title_elem = item.find('h2')
                if not title_elem: continue
                title = title_elem.get_text(strip=True)
                
                # Link
                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ""
                if url and not url.startswith('http'):
                    url = BASE_URL + url
                
                machine_id = hashlib.md5(url.encode()).hexdigest()
                
                # Price - usually hidden behind "Price info", but sometimes visible
                # Browser agent saw it in .btn-cta or just card text
                price = None
                currency = "EUR"
                price_text = item.get_text()
                # Attempt to find "€ 12,345" pattern
                import re
                price_match = re.search(r'([0-9.,]+)\s*€|€\s*([0-9.,]+)', price_text)
                if price_match:
                    p_str = price_match.group(1) or price_match.group(2)
                    try:
                        price = float(p_str.replace('.', '').replace(',', '.'))
                        # Filter out unlikely small numbers (year/model numbers misidentified)
                        if price < 100: price = None
                    except:
                        pass
                
                # Seller (Dealer info is often in the footer of the card)
                seller = "Unknown Seller"
                seller_elem = item.select_one('.dealer-name') or item.select_one('.w-100')
                if seller_elem:
                    seller = seller_elem.get_text(strip=True)

                # Year - Regex from card text
                year = None
                year_match = re.search(r'Year of construction:\s*(\d{4})', price_text)
                if year_match:
                    year = year_match.group(1)
                
                # Location - Regex or specific selector
                location = None
                # Simple heuristic for location (often Capitalized word + km)
                loc_match = re.search(r'([A-Za-z]+)\s*\n\s*\d+,?\d*\s*km', price_text)
                if loc_match:
                    location = loc_match.group(1)

                manufacturer = extract_manufacturer(title)
                model = extract_model(title)
                
                listings.append({
                    "machine_id": machine_id,
                    "title": title,
                    "category": category,
                    "manufacturer": manufacturer,
                    "model": model,
                    "seller": seller,
                    "source": "Machineseeker",
                    "listing_url": url,
                    "current_price": price,
                    "currency": currency,
                    "year": year,
                    "location": location,
                    "status": "Active"
                })
            except Exception as e:
                logger.error(f"Error parsing listing: {e}")
                continue
    except Exception as e:
        logger.error(f"Error parsing Machineseeker HTML: {e}")
    
    return listings

