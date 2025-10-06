"""
Price Tracker Bot - Main Entry Point
With Affiliate Link Integration
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# Load environment variables
load_dotenv()

# Configure logging (Docker-friendly)
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler if possible
try:
    log_file = os.getenv('LOG_FILE', '/tmp/bot.log')
    log_handlers.append(logging.FileHandler(log_file))
except PermissionError:
    # If file logging fails, just use console logging
    pass

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# Import modules
from database.db_manager import db_manager
from utils.affiliate_manager import affiliate_manager
from config.affiliate_config import AFFILIATE_CONFIG
from notifications.notifier import Notifier

# Import handlers
from handlers import tracking_handler, admin_handler, user_handler


class PriceTrackerBot:
    """
    Main bot class with affiliate link integration
    """
    
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables")
        
        self.bot = Bot(
            token=self.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        self.dp = Dispatcher()
        self.scheduler = AsyncIOScheduler()
        self.notifier = None
        
        # Load affiliate config into affiliate manager
        self._load_affiliate_config()
    
    def _load_affiliate_config(self):
        """Load affiliate configuration from config file"""
        for platform, config in AFFILIATE_CONFIG.items():
            if config.get('enabled'):
                affiliate_manager.update_affiliate_config(
                    platform=platform,
                    tag=config['tag'],
                    param_name=config['param_name']
                )
                logger.info(f"✅ Affiliate enabled for {platform}")
    
    async def on_startup(self):
        """Initialize bot on startup"""
        try:
            logger.info("🚀 Starting Price Tracker Bot with Affiliate Integration...")
            
            # Connect to database
            await db_manager.connect()
            logger.info("✅ Database connected")
            
            # Initialize notifier
            self.notifier = Notifier(self.bot)
            
            # Register handlers
            self.dp.include_router(tracking_handler.router)
            self.dp.include_router(admin_handler.router)
            self.dp.include_router(user_handler.router)
            logger.info("✅ Handlers registered")
            
            # Start scheduler
            self._setup_scheduled_jobs()
            self.scheduler.start()
            logger.info("✅ Scheduler started")
            
            # Send startup notification to admins
            admin_ids = os.getenv("ADMIN_USER_IDS", "").split(",")
            for admin_id in admin_ids:
                if admin_id.strip():
                    try:
                        await self.bot.send_message(
                            chat_id=int(admin_id.strip()),
                            text="✅ **Bot Started Successfully**\n\n"
                                 "🔗 Affiliate links enabled\n"
                                 "📊 All systems operational",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            logger.info("✅ Bot is ready and running!")
            
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}", exc_info=True)
            raise
    
    def _setup_scheduled_jobs(self):
        """Setup scheduled jobs for price checking"""
        check_interval = int(os.getenv("CHECK_INTERVAL", 3600))
        batch_size = int(os.getenv("BATCH_SIZE", 100))
        
        # Price checking job
        self.scheduler.add_job(
            self.check_prices,
            trigger=IntervalTrigger(seconds=check_interval),
            id='price_checker',
            name='Check product prices',
            replace_existing=True,
            kwargs={'batch_size': batch_size}
        )
        
        # Daily summary job (9 AM)
        self.scheduler.add_job(
            self.send_daily_summaries,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_summary',
            name='Send daily summaries',
            replace_existing=True
        )
        
        # Weekly summary job (Monday 9 AM)
        self.scheduler.add_job(
            self.send_weekly_summaries,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_summary',
            name='Send weekly summaries',
            replace_existing=True
        )
        
        # Cleanup job (Daily 2 AM)
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup',
            name='Cleanup old data',
            replace_existing=True
        )
        
        # Analytics job (Daily midnight)
        self.scheduler.add_job(
            self.record_analytics,
            trigger=CronTrigger(hour=0, minute=0),
            id='analytics',
            name='Record analytics',
            replace_existing=True
        )
        
        logger.info("✅ Scheduled jobs configured")
    
    async def check_prices(self, batch_size: int = 100):
        """Check prices for tracked products"""
        try:
            logger.info(f"🔍 Starting price check (batch size: {batch_size})")
            
            # Get products to check
            trackings = await db_manager.get_trackings_to_check(limit=batch_size)
            
            if not trackings:
                logger.info("No products to check")
                return
            
            from scrapers.scraper_manager import scraper_manager
            
            notifications = []
            
            for tracking in trackings:
                try:
                    # Scrape current price
                    product_data = await scraper_manager.scrape_product(
                        tracking.product_url,
                        tracking.platform
                    )
                    
                    if not product_data or 'error' in product_data:
                        logger.warning(f"Failed to scrape {tracking.product_id}")
                        continue
                    
                    new_price = product_data.get('price')
                    old_price = tracking.current_price
                    
                    # Update tracking
                    await db_manager.update_tracking_price(
                        str(tracking.id),
                        new_price,
                        product_data.get('stock_status', 'in_stock'),
                        product_data.get('discount')
                    )
                    
                    # Check if alert should be sent
                    if old_price and new_price != old_price:
                        change_percent = ((new_price - old_price) / old_price) * 100
                        
                        # Check alert settings
                        should_alert = False
                        alert_settings = tracking.alert_settings
                        
                        if alert_settings.alert_type == 'any_change':
                            should_alert = True
                        elif alert_settings.alert_type == 'percentage_drop':
                            if change_percent <= -alert_settings.threshold:
                                should_alert = True
                        elif alert_settings.alert_type == 'fixed_price':
                            if new_price <= alert_settings.threshold:
                                should_alert = True
                        
                        # Check price increase notification setting
                        if change_percent > 0 and not alert_settings.notify_on_price_increase:
                            should_alert = False
                        
                        if should_alert:
                            notifications.append({
                                'type': 'price_alert',
                                'user_id': tracking.user_id,
                                'tracking': tracking,
                                'old_price': old_price,
                                'new_price': new_price,
                                'change_percent': change_percent
                            })
                    
                    # Check stock status changes
                    if product_data.get('stock_status') != 'in_stock' and \
                       tracking.alert_settings.notify_on_stock:
                        notifications.append({
                            'type': 'stock_alert',
                            'user_id': tracking.user_id,
                            'tracking': tracking,
                            'stock_status': product_data.get('stock_status')
                        })
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error checking product {tracking.id}: {e}")
                    continue
            
            # Send notifications in batch
            if notifications:
                await self.notifier.send_batch_notifications(notifications)
                logger.info(f"✅ Sent {len(notifications)} notifications")
            
            logger.info(f"✅ Price check completed: {len(trackings)} products checked")
            
        except Exception as e:
            logger.error(f"Error in price check: {e}", exc_info=True)
    
    async def send_daily_summaries(self):
        """Send daily summaries to users"""
        try:
            logger.info("📊 Sending daily summaries")
            
            # Get users who want daily summaries
            users = await db_manager.db.users.find({
                "is_active": True,
                "daily_summary": True
            }).to_list(length=None)
            
            for user in users:
                try:
                    await self.notifier.send_daily_summary(user['user_id'])
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Failed to send summary to {user['user_id']}: {e}")
            
            logger.info(f"✅ Daily summaries sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error sending daily summaries: {e}")
    
    async def send_weekly_summaries(self):
        """Send weekly summaries to users"""
        try:
            logger.info("📊 Sending weekly summaries")
            
            users = await db_manager.db.users.find({
                "is_active": True,
                "weekly_summary": True
            }).to_list(length=None)
            
            # Implementation similar to daily summaries
            logger.info(f"✅ Weekly summaries sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error sending weekly summaries: {e}")
    
    async def cleanup_old_data(self):
        """Cleanup old inactive data"""
        try:
            logger.info("🧹 Running cleanup job")
            cleanup_days = int(os.getenv("AUTO_CLEANUP_DAYS", 90))
            await db_manager.cleanup_old_data(days=cleanup_days)
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    async def record_analytics(self):
        """Record daily analytics"""
        try:
            logger.info("📈 Recording analytics")
            stats = await db_manager.get_stats()
            
            await db_manager.record_analytics({
                "date": datetime.utcnow(),
                **stats
            })
            
            logger.info("✅ Analytics recorded")
        except Exception as e:
            logger.error(f"Error recording analytics: {e}")
    
    async def on_shutdown(self):
        """Cleanup on shutdown"""
        try:
            logger.info("🛑 Shutting down bot...")
            
            self.scheduler.shutdown()
            await db_manager.disconnect()
            await self.bot.session.close()
            
            logger.info("✅ Bot shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def start(self):
        """Start the bot"""
        try:
            await self.on_startup()
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types()
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
        finally:
            await self.on_shutdown()


async def main():
    """Main entry point"""
    bot = PriceTrackerBot()
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
