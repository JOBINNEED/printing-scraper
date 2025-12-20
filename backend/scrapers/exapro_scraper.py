import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List
import hashlib
from .common import extract_manufacturer, extract_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.exapro.com"

async def scrape() -> List[dict]:
    listings = []
    
    try:
        categories = [
            "/offset-printing-machine-l1_2304/",
            "/digital-printing-machine-l1_2305/",
            "/packaging-machine-l1_169/",
            "/flexographic-printing-machine-l1_2307/"
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            for category in categories:
                try:
                    url = f"{BASE_URL}{category}"
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            html = await response.text()
                            category_name = category.split('/')[1].replace('-', ' ').title()
                            category_listings = parse_listings(html, category_name)
                            listings.extend(category_listings)
                            logger.info(f"Exapro - Found {len(category_listings)} listings in {category}")
                        else:
                            logger.warning(f"Exapro - Failed to fetch {category}: status {response.status}")
                except Exception as e:
                    logger.error(f"Exapro - Error fetching {category}: {e}")
        
        logger.info(f"Exapro - Total listings found: {len(listings)}")
        
        if len(listings) == 0:
            logger.warning("Exapro scraper returned 0 results!")
        
    except Exception as e:
        logger.error(f"Exapro scraper error: {e}")
    
    return listings

def parse_listings(html: str, category: str) -> List[dict]:
    listings = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        items = soup.find_all('div', class_='product-item') or soup.find_all('div', class_='listing')
        
        for item in items[:20]:
            try:
                title_elem = item.find('h2') or item.find('h3') or item.find('a', class_='product-title')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Machine"
                
                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ""
                if url and not url.startswith('http'):
                    url = BASE_URL + url
                
                machine_id = hashlib.md5(url.encode()).hexdigest() if url else hashlib.md5(title.encode()).hexdigest()
                
                price_elem = item.find('span', class_='price') or item.find(text=lambda t: t and ('€' in str(t) or 'EUR' in str(t)))
                price = None
                currency = "EUR"
                if price_elem:
                    price_text = str(price_elem).strip().replace(',', '').replace('.', '').replace('€', '').replace('EUR', '').strip()
                    try:
                        price = float(price_text) if price_text.isdigit() else None
                    except:
                        price = None
                
                seller_elem = item.find('div', class_='seller') or item.find('span', class_='dealer')
                seller = seller_elem.get_text(strip=True) if seller_elem else "Unknown Seller"
                
                year_elem = item.find(text=lambda t: t and any(str(y) in str(t) for y in range(1980, 2030)))
                year = None
                if year_elem:
                    for y in range(2024, 1980, -1):
                        if str(y) in str(year_elem):
                            year = str(y)
                            break
                
                location_elem = item.find('span', class_='location')
                location = location_elem.get_text(strip=True) if location_elem else None
                
                manufacturer = extract_manufacturer(title)
                model = extract_model(title)
                
                listings.append({
                    "machine_id": machine_id,
                    "title": title,
                    "category": category,
                    "manufacturer": manufacturer,
                    "model": model,
                    "seller": seller,
                    "source": "Exapro",
                    "listing_url": url,
                    "current_price": price,
                    "currency": currency,
                    "year": year,
                    "location": location
                })
            except Exception as e:
                logger.error(f"Error parsing individual listing: {e}")
    
    except Exception as e:
        logger.error(f"Error parsing Exapro HTML: {e}")
    
    return listings

