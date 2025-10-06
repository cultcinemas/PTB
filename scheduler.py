import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from db_manager import MongoManager
from scraper import Scraper
from notifications import send_price_alert, send_trending_deals
from config import SCRAPE_INTERVAL, INACTIVITY_DAYS

class BotScheduler:
    def __init__(self):
        self.db = MongoManager()
        self.scraper = Scraper()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.run_scraper, "interval", minutes=SCRAPE_INTERVAL)
        self.scheduler.add_job(self.cleanup_inactive_users, "interval", hours=24)
        self.scheduler.add_job(self.update_trending_deals, "interval", hours=24)

    async def run_scraper(self):
        products = list(self.db.products.find({"active": True}))
        urls = [p["url"] for p in products]
        if not urls:
            return
        results = await self.scraper.scrape_all(urls)

        for result in results:
            product = self.db.products.find_one({"url": result["url"]})
            if not product:
                continue
            old_price = product.get("price", 0)
            new_price = result["price"]
            if old_price != new_price:
                self.db.products.update_one(
                    {"url": result["url"]},
                    {"$set": {"price": new_price, "last_checked": datetime.utcnow()}}
                )
                await send_price_alert(product["user_id"], product, old_price, new_price)

    def cleanup_inactive_users(self):
        deleted_count = self.db.cleanup_inactive_users()
        print(f"[{datetime.utcnow()}] Auto-deleted {deleted_count} inactive users.")

    async def update_trending_deals(self):
        # Calculate top price drops in last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        recent_products = list(self.db.products.find({"last_checked": {"$gte": since}}))
        trending = sorted(recent_products, key=lambda x: x.get("price_change", 0), reverse=True)[:10]
        for user_id in self.db.users.distinct("user_id"):
            await send_trending_deals(user_id, trending)

    def start(self):
        self.scheduler.start()
        print("Scheduler started!")
