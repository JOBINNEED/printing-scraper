import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

manufacturers = ['Heidelberg', 'Komori', 'Manroland', 'KBA', 'Bobst', 'HP', 'Canon', 'Xerox']
categories = ['Offset Presses', 'Digital Presses', 'Packaging Machines', 'Printing Machines', 'Finishing Equipment']
sellers = ['PrintTech GmbH', 'MachineWorld Ltd', 'Euro Machinery', 'Global Print Solutions', 'Industrial Equipment Co']
sources = ['Machineseeker', 'Exapro']

async def seed_data():
    now = datetime.now(timezone.utc)
    
    # Clear existing data
    await db.machines.delete_many({})
    await db.price_history.delete_many({})
    await db.scraper_logs.delete_many({})
    
    print("Generating sample machinery listings...")
    
    machines = []
    
    # Generate 50 sample machines
    for i in range(50):
        manufacturer = random.choice(manufacturers)
        category = random.choice(categories)
        model_num = random.randint(1000, 9999)
        
        days_ago = random.randint(0, 30)
        first_seen = now - timedelta(days=days_ago)
        
        # Some machines might be "Possibly Sold" or "Removed"
        status_roll = random.random()
        if status_roll > 0.85:
            status = "Possibly Sold"
            last_seen = now - timedelta(days=random.randint(4, 6))
        elif status_roll > 0.75:
            status = "Removed"
            last_seen = now - timedelta(days=random.randint(8, 14))
        else:
            status = "Active"
            last_seen = now - timedelta(hours=random.randint(0, 48))
        
        base_price = random.randint(50000, 500000)
        
        machine_id = f"machine_{i+1:04d}"
        
        machine = {
            "machine_id": machine_id,
            "title": f"{manufacturer} {category.split()[0]} {model_num}",
            "category": category,
            "manufacturer": manufacturer,
            "model": f"Model {model_num}",
            "seller": random.choice(sellers),
            "source": random.choice(sources),
            "listing_url": f"https://example.com/listing/{machine_id}",
            "first_seen": first_seen.isoformat(),
            "last_seen": last_seen.isoformat(),
            "status": status,
            "current_price": base_price,
            "currency": "EUR",
            "year": str(random.randint(2010, 2023)),
            "location": random.choice(["Germany", "France", "Italy", "Spain", "UK"])
        }
        
        machines.append(machine)
        
        # Add price history (some machines have price changes)
        if random.random() > 0.7:  # 30% have price changes
            num_changes = random.randint(1, 3)
            for j in range(num_changes):
                price_date = first_seen + timedelta(days=random.randint(1, days_ago))
                price_variation = random.uniform(-0.15, 0.05)  # Mostly price drops
                price = int(base_price * (1 + price_variation))
                
                await db.price_history.insert_one({
                    "machine_id": machine_id,
                    "price": price,
                    "currency": "EUR",
                    "timestamp": price_date.isoformat()
                })
        
        # Add current price to history
        await db.price_history.insert_one({
            "machine_id": machine_id,
            "price": base_price,
            "currency": "EUR",
            "timestamp": last_seen.isoformat()
        })
    
    # Insert all machines
    await db.machines.insert_many(machines)
    print(f"✓ Inserted {len(machines)} sample machines")
    
    # Add scraper logs
    for source in ['Machineseeker', 'Exapro']:
        await db.scraper_logs.insert_one({
            "source": source,
            "listings_found": 25,
            "timestamp": now.isoformat(),
            "status": "success",
            "message": f"Processed 25 listings (Demo Data)"
        })
    
    print("✓ Added scraper logs")
    print(f"✓ Seed data complete! Generated {len(machines)} machines with price history")
    
    # Print summary
    active = sum(1 for m in machines if m['status'] == 'Active')
    sold = sum(1 for m in machines if m['status'] == 'Possibly Sold')
    removed = sum(1 for m in machines if m['status'] == 'Removed')
    
    print(f"\nStatus breakdown:")
    print(f"  Active: {active}")
    print(f"  Possibly Sold: {sold}")
    print(f"  Removed: {removed}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
