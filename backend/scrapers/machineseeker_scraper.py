import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List
import hashlib

logger = logging.getLogger(__name__)

BASE_URL = "https://www.machineseeker.com"

async def scrape() -> List[dict]:
    listings = []
    
    try:
        categories = [
            "/offset-presses",
            "/digital-presses",
            "/packaging-machines",
            "/printing-machines"
        ]
        
        async with aiohttp.ClientSession() as session:
            for category in categories:
                try:
                    url = f"{BASE_URL}{category}"
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            html = await response.text()
                            category_listings = parse_listings(html, category.strip('/').replace('-', ' ').title())
                            listings.extend(category_listings)
                            logger.info(f"Machineseeker - Found {len(category_listings)} listings in {category}")
                        else:
                            logger.warning(f"Machineseeker - Failed to fetch {category}: status {response.status}")
                except Exception as e:
                    logger.error(f"Machineseeker - Error fetching {category}: {e}")
        
        logger.info(f"Machineseeker - Total listings found: {len(listings)}")
        
        if len(listings) == 0:
            logger.warning("Machineseeker scraper returned 0 results!")
        
    except Exception as e:
        logger.error(f"Machineseeker scraper error: {e}")
    
    return listings

def parse_listings(html: str, category: str) -> List[dict]:
    listings = []
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        items = soup.find_all('div', class_='machine-item') or soup.find_all('article')
        
        for item in items[:20]:
            try:
                title_elem = item.find('h3') or item.find('h2') or item.find('a')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Machine"
                
                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ""
                if url and not url.startswith('http'):
                    url = BASE_URL + url
                
                machine_id = hashlib.md5(url.encode()).hexdigest() if url else hashlib.md5(title.encode()).hexdigest()
                
                price_elem = item.find(text=lambda t: t and ('€' in str(t) or 'EUR' in str(t)))
                price = None
                currency = "EUR"
                if price_elem:
                    price_text = price_elem.strip().replace(',', '').replace('.', '').replace('€', '').replace('EUR', '').strip()
                    try:
                        price = float(price_text) if price_text.isdigit() else None
                    except:
                        price = None
                
                seller_elem = item.find('span', class_='dealer') or item.find(text=lambda t: t and 'Dealer' in str(t))
                seller = seller_elem.get_text(strip=True) if seller_elem else "Unknown Seller"
                
                year_elem = item.find(text=lambda t: t and any(str(y) in str(t) for y in range(1980, 2030)))
                year = None
                if year_elem:
                    for y in range(2024, 1980, -1):
                        if str(y) in str(year_elem):
                            year = str(y)
                            break
                
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
                    "location": None
                })
            except Exception as e:
                logger.error(f"Error parsing individual listing: {e}")
    
    except Exception as e:
        logger.error(f"Error parsing Machineseeker HTML: {e}")
    
    return listings

def extract_manufacturer(title: str) -> str:
    manufacturers = [
        'Heidelberg', 'Komori', 'Manroland', 'KBA', 'Bobst', 'HP', 'Canon', 
        'Xerox', 'Konica', 'Ricoh', 'Roland', 'MAN', 'Mitsubishi', 'Ryobi',
        'Hamada', 'Sakurai', 'Adast', 'Planeta', 'Solna', 'Goss'
    ]
    
    title_upper = title.upper()
    for mfr in manufacturers:
        if mfr.upper() in title_upper:
            return mfr
    
    return None

def extract_model(title: str) -> str:
    parts = title.split()
    if len(parts) > 1:
        for i, part in enumerate(parts):
            if any(char.isdigit() for char in part) and len(part) > 2:
                return ' '.join(parts[i:i+2])
    return None
