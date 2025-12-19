# MarketIntel - Industrial Machinery Market Intelligence Platform

A business-grade, interactive web application for tracking used industrial printing and packaging machinery listings across multiple marketplaces.

## Overview

MarketIntel replaces manual daily searching with an automated, professional dashboard that:
- Tracks machinery listings from Machineseeker and Exapro
- Detects price changes and likely sold items
- Provides advanced filtering and search
- Shows price history and market trends
- Supports easy expansion to additional sources

## Features

### Dashboard
- **Market Overview**: New listings, price drops, likely sold items, active listings
- **Category Breakdown**: Equipment distribution by type
- **Quick Actions**: Fast access to filtered views

### All Listings
- **Interactive Table**: Sortable, filterable data grid
- **Filters**: Category, manufacturer, seller, status
- **Search**: Full-text search by title or model
- **Status Badges**: Active, Possibly Sold, Removed

### Machine Detail
- **Complete Information**: All listing details
- **Price History Chart**: Visual timeline of price changes
- **Status Timeline**: First seen / last seen tracking
- **Direct Links**: Quick access to original listings

### Settings
- **Manual Scraper**: Trigger on-demand data refresh
- **Automated Schedule**: Daily scraping at midnight
- **Scraper Logs**: Full history of scraping activity

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React 19 with Shadcn UI
- **Database**: MongoDB
- **Scrapers**: aiohttp + BeautifulSoup
- **Charts**: Recharts
- **Styling**: Tailwind CSS

## Data Sources

### Phase 1 (Implemented)
- Machineseeker
- Exapro
- Kitmondo (Experimental)

### Future Expansion
- MachinePoint
- PressXchange
- Auction sources (RSS/email)

## Status Detection Logic

- **Active**: Listing appeared in latest scrape
- **Possibly Sold**: Missing for 3 consecutive days
- **Removed**: Missing for 7+ days

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB

### Windows Installation

1. **Install MongoDB**
   ```
   Download and install MongoDB Community Server
   ```

2. **Install Python Dependencies**
   ```bash
   cd /app/backend
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd /app/frontend
   yarn install
   ```

4. **Configure Environment**
   - Backend: `/app/backend/.env`
   - Frontend: `/app/frontend/.env`

5. **Start Application**
   ```bash
   # Easy way
   start_marketintel.bat

   # Or manually
   # Terminal 1: MongoDB
   mongod --dbpath /data/db

   # Terminal 2: Backend
   cd /app/backend
   uvicorn server:app --host 0.0.0.0 --port 8001

   # Terminal 3: Frontend
   cd /app/frontend
   yarn start
   ```

6. **Access Application**
   - Dashboard: http://localhost:3000
   - API Docs: http://localhost:8001/docs

## Usage

### First Run
1. Navigate to Settings page
2. Click "Run Scrapers Now"
3. Wait for scrapers to complete
4. View results in Dashboard and All Listings

### Daily Monitoring
1. Open Dashboard
2. Check new listings and price drops
3. Review "Possibly Sold" items
4. Filter by category or manufacturer
5. Click listings for detailed view

### Search & Filter
- Use search bar for specific models
- Filter by category, manufacturer, seller, status
- Sort by last seen, first seen, or price
- Clear filters to see all listings

## API Endpoints

### Dashboard
- `GET /api/dashboard/overview` - Market overview stats

### Machines
- `GET /api/machines` - List all machines (with filters)
- `GET /api/machines/{id}` - Get machine details
- `GET /api/machines/{id}/price-history` - Get price history

### Scrapers
- `POST /api/scrapers/run` - Trigger manual scrape
- `GET /api/scrapers/logs` - View scraper logs

### Filters
- `GET /api/filters/options` - Get filter options

## Database Schema

### Machines Collection
```javascript
{
  machine_id: string,
  title: string,
  category: string,
  manufacturer: string,
  model: string,
  seller: string,
  source: string,
  listing_url: string,
  first_seen: datetime,
  last_seen: datetime,
  status: string,
  current_price: float,
  currency: string,
  year: string,
  location: string
}
```

### Price History Collection
```javascript
{
  machine_id: string,
  price: float,
  currency: string,
  timestamp: datetime
}
```

### Scraper Logs Collection
```javascript
{
  source: string,
  listings_found: int,
  timestamp: datetime,
  status: string,
  message: string
}
```

## Design Guidelines

- **Theme**: Swiss & High-Contrast (data-focused)
- **Fonts**: Chivo (headings), IBM Plex Sans (body), JetBrains Mono (data)
- **Colors**: Slate/White base with Safety Orange for alerts
- **Layout**: Dense, professional, no wasted space

## Development Notes

### Adding New Scrapers

1. Create scraper file in `/app/backend/scrapers/`
2. Implement `async def scrape() -> List[dict]`
3. Import in `server.py`
4. Add to `run_scrapers()` function

### Scraper Template
```python
import aiohttp
from bs4 import BeautifulSoup
from typing import List

async def scrape() -> List[dict]:
    listings = []
    # Scraping logic here
    return listings
```

## Production Deployment

1. Update `.env` files with production values
2. Use PostgreSQL instead of MongoDB (schema compatible)
3. Add authentication (JWT recommended)
4. Set up reverse proxy (nginx)
5. Enable HTTPS
6. Configure automated backups

## Testing

### Seed Sample Data
```bash
cd /app/backend
python seed_data.py
```

### Manual API Testing
```bash
curl http://localhost:8001/api/dashboard/overview
curl http://localhost:8001/api/machines
```

## Success Criteria

✅ Non-technical users can monitor machinery market daily
✅ New listings, price changes, sold items immediately visible
✅ Professional equipment-tracking platform experience
✅ No manual CSV file handling required
✅ Fast filtering and sorting
✅ Clear visual hierarchy

## Future Enhancements

- Email notifications for new listings / price drops
- Saved searches and alerts
- Export to CSV/Excel
- User authentication and preferences
- Mobile app
- Machine learning for price predictions
- Comparison tool for similar machines
- Seller reputation tracking

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact: support@marketintel.local
