import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List
import hashlib
from .common import extract_manufacturer, extract_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kitmondo.com"

async def scrape() -> List[dict]:
    listings = []

    try:
        # Kitmondo categories often follow pattern /category-name/c{id}
        # Using a general search or known category for printing
        categories = [
            "/printing-equipment/c45",
            "/packaging-equipment/c49"
        ]

        async with aiohttp.ClientSession() as session:
            for category in categories:
                try:
                    url = f"{BASE_URL}{category}"
                    # Use a standard user agent to mimic a browser
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    async with session.get(url, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            html = await response.text()
                            category_name = "Printing Equipment" if "printing" in category else "Packaging Equipment"
                            category_listings = parse_listings(html, category_name)
                            listings.extend(category_listings)
                            logger.info(f"Kitmondo - Found {len(category_listings)} listings in {category}")
                        elif response.status in [403, 401]:
                            logger.warning(f"Kitmondo - Access denied ({response.status}) for {category}. This is expected if scraping is blocked.")
                        else:
                            logger.warning(f"Kitmondo - Failed to fetch {category}: status {response.status}")
                except Exception as e:
                    logger.error(f"Kitmondo - Error fetching {category}: {e}")

        logger.info(f"Kitmondo - Total listings found: {len(listings)}")

    except Exception as e:
        logger.error(f"Kitmondo scraper error: {e}")

    return listings

def parse_listings(html: str, category: str) -> List[dict]:
    listings = []

    try:
        soup = BeautifulSoup(html, 'lxml')

        # Hypothetical selectors based on common e-commerce structures
        # In a real scenario, these would be reverse-engineered from the actual page
        items = soup.find_all('div', class_='listing-item') or \
                soup.find_all('div', class_='product-card') or \
                soup.find_all('article')

        for item in items[:20]:
            try:
                title_elem = item.find('h3') or item.find('h2') or item.find('a', class_='title')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Machine"

                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ""
                if url and not url.startswith('http'):
                    url = BASE_URL + url

                machine_id = hashlib.md5(url.encode()).hexdigest() if url else hashlib.md5(title.encode()).hexdigest()

                # Price extraction
                price_elem = item.find(text=lambda t: t and ('$' in str(t) or '€' in str(t) or 'USD' in str(t) or 'EUR' in str(t)))
                price = None
                currency = "USD" # Default assumption for Kitmondo
                if price_elem:
                    price_text = str(price_elem).strip()
                    if '€' in price_text or 'EUR' in price_text:
                        currency = "EUR"

                    # specific cleaning
                    clean_price = ''.join(c for c in price_text if c.isdigit() or c == '.')
                    try:
                        price = float(clean_price)
                    except:
                        price = None

                seller_elem = item.find('div', class_='seller-name') or item.find('span', class_='vendor')
                seller = seller_elem.get_text(strip=True) if seller_elem else "Unknown Seller"

                year = None
                # Basic year extraction from title
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', title)
                if year_match:
                    year = year_match.group(0)

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
                    "source": "Kitmondo",
                    "listing_url": url,
                    "current_price": price,
                    "currency": currency,
                    "year": year,
                    "location": location
                })
            except Exception as e:
                logger.error(f"Error parsing individual Kitmondo listing: {e}")

    except Exception as e:
        logger.error(f"Error parsing Kitmondo HTML: {e}")

    return listings
