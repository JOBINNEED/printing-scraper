from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
from scrapers import machineseeker_scraper, exapro_scraper, kitmondo_scraper, pressxchange_scraper
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Machine(BaseModel):
    model_config = ConfigDict(extra="ignore")
    machine_id: str
    title: str
    category: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    seller: str
    source: str
    listing_url: str
    first_seen: datetime
    last_seen: datetime
    status: str
    current_price: Optional[float] = None
    currency: Optional[str] = None
    year: Optional[str] = None
    location: Optional[str] = None

class PriceHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    machine_id: str
    price: float
    currency: str
    timestamp: datetime

class ScraperLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: str
    listings_found: int
    timestamp: datetime
    status: str
    message: str

class DashboardOverview(BaseModel):
    new_listings: int
    price_drops: int
    likely_sold: int
    total_active: int
    category_counts: dict

class ScraperResponse(BaseModel):
    status: str
    message: str
    listings_processed: int

@api_router.get("/")
async def root():
    return {"message": "MarketIntel API"}

@api_router.get("/dashboard/overview", response_model=DashboardOverview)
async def get_dashboard_overview():
    try:
        now = datetime.now(timezone.utc)
        yesterday = datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp()
        
        new_listings = await db.machines.count_documents({
            "first_seen": {"$gte": datetime.fromtimestamp(yesterday, tz=timezone.utc)}
        })
        
        price_drops_cursor = db.price_history.aggregate([
            {"$sort": {"machine_id": 1, "timestamp": -1}},
            {"$group": {
                "_id": "$machine_id",
                "prices": {"$push": "$price"}
            }},
            {"$match": {
                "prices.1": {"$exists": True},
                "$expr": {"$lt": [{"$arrayElemAt": ["$prices", 0]}, {"$arrayElemAt": ["$prices", 1]}]}
            }}
        ])
        price_drops = len(await price_drops_cursor.to_list(1000))
        
        likely_sold = await db.machines.count_documents({"status": "Possibly Sold"})
        total_active = await db.machines.count_documents({"status": "Active"})
        
        category_pipeline = [
            {"$match": {"status": "Active"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        categories = await db.machines.aggregate(category_pipeline).to_list(100)
        category_counts = {cat["_id"]: cat["count"] for cat in categories}
        
        return DashboardOverview(
            new_listings=new_listings,
            price_drops=price_drops,
            likely_sold=likely_sold,
            total_active=total_active,
            category_counts=category_counts
        )
    except Exception as e:
        logger.error(f"Error in dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/machines", response_model=List[Machine])
async def get_machines(
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    seller: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "last_seen",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 50
):
    try:
        query = {}
        if category:
            query["category"] = category
        if manufacturer:
            query["manufacturer"] = manufacturer
        if seller:
            query["seller"] = seller
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"model": {"$regex": search, "$options": "i"}}
            ]
        
        sort_direction = -1 if sort_order == "desc" else 1
        
        machines = await db.machines.find(query, {"_id": 0}).sort(
            sort_by, sort_direction
        ).skip(skip).limit(limit).to_list(limit)
        
        for machine in machines:
            for date_field in ['first_seen', 'last_seen']:
                if isinstance(machine.get(date_field), str):
                    machine[date_field] = datetime.fromisoformat(machine[date_field])
        
        return machines
    except Exception as e:
        logger.error(f"Error fetching machines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/machines/{machine_id}", response_model=Machine)
async def get_machine(machine_id: str):
    try:
        machine = await db.machines.find_one({"machine_id": machine_id}, {"_id": 0})
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        for date_field in ['first_seen', 'last_seen']:
            if isinstance(machine.get(date_field), str):
                machine[date_field] = datetime.fromisoformat(machine[date_field])
        
        return machine
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/machines/{machine_id}/price-history", response_model=List[PriceHistory])
async def get_price_history(machine_id: str):
    try:
        history = await db.price_history.find(
            {"machine_id": machine_id}, {"_id": 0}
        ).sort("timestamp", 1).to_list(1000)
        
        for record in history:
            if isinstance(record.get('timestamp'), str):
                record['timestamp'] = datetime.fromisoformat(record['timestamp'])
        
        return history
    except Exception as e:
        logger.error(f"Error fetching price history for {machine_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scrapers/run", response_model=ScraperResponse)
async def run_scrapers():
    try:
        total_processed = 0
        
        logger.info("Starting Machineseeker scraper...")
        ms_listings = await machineseeker_scraper.scrape()
        ms_count = await process_listings(ms_listings, "Machineseeker")
        total_processed += ms_count
        
        await db.scraper_logs.insert_one({
            "source": "Machineseeker",
            "listings_found": ms_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "message": f"Processed {ms_count} listings"
        })
        
        # Exapro Scraper Removed
        
        
        logger.info("Starting Kitmondo scraper...")
        kit_listings = await kitmondo_scraper.scrape()
        kit_count = await process_listings(kit_listings, "Kitmondo")
        total_processed += kit_count
        
        await db.scraper_logs.insert_one({
            "source": "Kitmondo",
            "listings_found": kit_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "message": f"Processed {kit_count} listings"
        })

        # Exapro removed per user request (redundant with Kitmondo)
        
        logger.info("Starting PressXchange scraper...")
        px_listings = await pressxchange_scraper.scrape()
        px_count = await process_listings(px_listings, "PressXchange")
        total_processed += px_count

        await db.scraper_logs.insert_one({
            "source": "PressXchange",
            "listings_found": px_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "message": f"Processed {px_count} listings"
        })
        
        await update_machine_status()
        
        return ScraperResponse(
            status="success",
            message=f"Scrapers completed successfully",
            listings_processed=total_processed
        )
    except Exception as e:
        logger.error(f"Error running scrapers: {e}")
        await db.scraper_logs.insert_one({
            "source": "All",
            "listings_found": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))

async def process_listings(listings: List[dict], source: str) -> int:
    now = datetime.now(timezone.utc)
    processed = 0
    
    for listing in listings:
        try:
            existing = await db.machines.find_one({"machine_id": listing["machine_id"]})
            
            if existing:
                update_data = {
                    "last_seen": now.isoformat(),
                    "status": "Active"
                }
                
                if listing.get("current_price") and listing["current_price"] != existing.get("current_price"):
                    update_data["current_price"] = listing["current_price"]
                    await db.price_history.insert_one({
                        "machine_id": listing["machine_id"],
                        "price": listing["current_price"],
                        "currency": listing.get("currency", "EUR"),
                        "timestamp": now.isoformat()
                    })
                
                await db.machines.update_one(
                    {"machine_id": listing["machine_id"]},
                    {"$set": update_data}
                )
            else:
                machine_data = {
                    **listing,
                    "first_seen": now.isoformat(),
                    "last_seen": now.isoformat(),
                    "status": "Active"
                }
                await db.machines.insert_one(machine_data)
                
                if listing.get("current_price"):
                    await db.price_history.insert_one({
                        "machine_id": listing["machine_id"],
                        "price": listing["current_price"],
                        "currency": listing.get("currency", "EUR"),
                        "timestamp": now.isoformat()
                    })
            
            processed += 1
        except Exception as e:
            logger.error(f"Error processing listing {listing.get('machine_id')}: {e}")
    
    return processed

async def update_machine_status():
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=3)
    
    await db.machines.update_many(
        {
            "last_seen": {"$lt": threshold.isoformat()},
            "status": "Active"
        },
        {"$set": {"status": "Possibly Sold"}}
    )
    
    removed_threshold = now - timedelta(days=7)
    await db.machines.update_many(
        {
            "last_seen": {"$lt": removed_threshold.isoformat()},
            "status": "Possibly Sold"
        },
        {"$set": {"status": "Removed"}}
    )

@api_router.get("/scrapers/logs", response_model=List[ScraperLog])
async def get_scraper_logs(limit: int = 50):
    try:
        logs = await db.scraper_logs.find({}, {"_id": 0}).sort(
            "timestamp", -1
        ).limit(limit).to_list(limit)
        
        for log in logs:
            if isinstance(log.get('timestamp'), str):
                log['timestamp'] = datetime.fromisoformat(log['timestamp'])
        
        return logs
    except Exception as e:
        logger.error(f"Error fetching scraper logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/filters/options")
async def get_filter_options():
    try:
        categories = await db.machines.distinct("category")
        manufacturers = await db.machines.distinct("manufacturer")
        sellers = await db.machines.distinct("seller")
        
        return {
            "categories": sorted([c for c in categories if c]),
            "manufacturers": sorted([m for m in manufacturers if m]),
            "sellers": sorted([s for s in sellers if s]),
            "statuses": ["Active", "Possibly Sold", "Removed"]
        }
    except Exception as e:
        logger.error(f"Error fetching filter options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

async def scheduled_scrape():
    logger.info("Running scheduled scrape...")
    try:
        await run_scrapers()
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(scheduled_scrape, 'cron', hour=0, minute=0)
    scheduler.start()
    logger.info("Scheduler started - daily scrapes at midnight")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()
