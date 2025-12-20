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

BASE_URL = "https://www.kitmondo.com"

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

def scrape_sync() -> List[dict]:
    listings = []
    driver = None
    try:
        # Step 1: Get subcategories
        main_category_url = "/used-printing-machinery/"
        url = f"{BASE_URL}{main_category_url}"
        logger.info(f"Kitmondo - Starting Selenium for {url}")
        
        driver = get_driver()
        driver.get(url)
        time.sleep(3) # Wait for JS
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        # Scrape main page listings first (Browser confirmed 30+ items here)
        main_listings = parse_listings(html, "General Printing")
        if main_listings:
             listings.extend(main_listings)
             logger.info(f"Kitmondo - Found {len(main_listings)} listings on main page")

        # Browser agent found categories in main area, not just valid list
        # Selectors: a[href*="/used-printing-machines-"], a[href^="/digital-printing-presses-"], etc.
        # We will use a broader verification: any link containing key keywords or starting with specific paths
        links = soup.select('a')
        for link in links:
             href = link.get('href', '')
             if not href: continue
             
             # Filter based on browser agent findings
             is_category = (
                 '/used-printing-machines-' in href or 
                 '/digital-printing-presses-' in href or 
                 '/4-colour-printing-press/' in href or
                 '/binding-saddle-stitchers/' in href
             )
             
             if is_category and href not in subcategories:
                 subcategories.append(href)
        
        # Limit to 5 to avoid long runtimes during testing (User wants quick check)
        subcategories = list(set(subcategories))[:5]
        
        # If no subcategories found, try the main page itself as a fallback
        if not subcategories:
            subcategories = [main_category_url]
            
        logger.info(f"Kitmondo - Found {len(subcategories)} subcategories")
        
        # Step 2: Scrape subcategories
        for category in subcategories:
            try:
                cat_url = f"{BASE_URL}{category}" if not category.startswith("http") else category
                logger.info(f"Kitmondo - Visiting {cat_url}")
                driver.get(cat_url)
                
                # Scroll
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                cat_html = driver.page_source
                cat_name = category.split('/')[-2].replace('-', ' ').title() if len(category.split('/')) > 2 else "Printing Machinery"
                
                cat_listings = parse_listings(cat_html, cat_name)
                listings.extend(cat_listings)
                logger.info(f"Kitmondo - Found {len(cat_listings)} listings in {cat_name}")
                
            except Exception as e:
                logger.error(f"Kitmondo - Error scraping category {category}: {e}")
                
    except Exception as e:
        logger.error(f"Kitmondo scraper error: {e}")
    finally:
        if driver:
             try:
                driver.quit()
             except:
                pass
                
    return listings

async def scrape() -> List[dict]:
    loop = asyncio.get_running_loop()
    # Run synchronous Selenium in a thread
    return await loop.run_in_executor(None, scrape_sync)

def parse_listings(html: str, category: str) -> List[dict]:
    listings = []
    try:
        soup = BeautifulSoup(html, 'lxml')
        # Verified selector from browser agent
        # .ps-product__title__list was found for titles, so the container is likely .ps-product--wide or .ps-product
        items = soup.select('.ps-product') or soup.select('.ps-product--wide') or soup.select('.product-item')
        
        # Fallback for list view
        if not items:
            items = soup.select('.listing-item') or soup.select('div[class*="product"]')
        
        for item in items[:20]:
            try:
                # Title - h2 or specific class found by agent
                title_elem = item.select_one('.ps-product__title') or \
                             item.select_one('.ps-product__title__list') or \
                             item.find('h2') or \
                             item.find('h4')
                
                if not title_elem: continue
                title = title_elem.get_text(strip=True)
                
                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ""
                if url and not url.startswith('http'):
                    url = BASE_URL + url
                    
                machine_id = hashlib.md5(url.encode()).hexdigest()
                
                # Price extraction
                price = None
                price_elem = item.select_one('.ps-product__price')
                price_text = price_elem.get_text(strip=True) if price_elem else item.get_text()
                
                # Try validation logic
                import re
                # Look for number usually with comma/dot and currency
                # E.g. € 12,000 or 4,500 €
                price_match = re.search(r'([0-9.,]+)\s*€|€\s*([0-9.,]+)', price_text)
                if price_match:
                    p_str = price_match.group(1) or price_match.group(2)
                    try:
                        price = float(p_str.replace(',', ''))
                    except:
                        pass
                
                # Year extraction from text
                year = None
                year_match = re.search(r'Year\s*:\s*(\d{4})|\b(19|20)\d{2}\b', item.get_text())
                if year_match:
                    year = year_match.group(1) or year_match.group(0)

                listings.append({
                    "machine_id": machine_id,
                    "title": title,
                    "category": category,
                    "manufacturer": extract_manufacturer(title),
                    "model": extract_model(title),
                    "seller": "Kitmondo",
                    "source": "Kitmondo",
                    "listing_url": url,
                    "current_price": price,
                    "currency": "USD", 
                    "year": year,
                    "location": None,
                    "status": "Active"
                })
            except Exception as e:
                continue
                
    except Exception as e:
        logger.error(f"Error parsing Kitmondo HTML: {e}")
        
    return listings
