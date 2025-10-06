"""
Migration script to add affiliate URLs to existing trackings
"""
import asyncio
import logging
from datetime import datetime
from database.db_manager import db_manager
from utils.affiliate_manager import affiliate_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_trackings():
    """Migrate existing trackings to include affiliate URLs"""
    try:
        logger.info("🚀 Starting migration...")
        
        # Connect to database
        await db_manager.connect()
        logger.info("✅ Database connected")
        
        # Find trackings without affiliate_url
        trackings = await db_manager.db.trackings.find({
            "$or": [
                {"affiliate_url": {"$exists": False}},
                {"original_url": {"$exists": False}}
            ]
        }).to_list(length=None)
        
        total = len(trackings)
        logger.info(f"📊 Found {total} trackings to migrate")
        
        if total == 0:
            logger.info("✅ No migration needed!")
            return
        
        success = 0
        failed = 0
        
        for i, tracking in enumerate(trackings, 1):
            try:
                product_url = tracking.get('product_url')
                platform = tracking.get('platform')
                
                if not product_url or not platform:
                    logger.warning(f"⚠️ Skipping tracking {tracking['_id']}: Missing URL or platform")
                    failed += 1
                    continue
                
                # Generate affiliate URL
                affiliate_url = affiliate_manager.convert_to_affiliate(
                    product_url,
                    platform
                )
                
                # Update database
                await db_manager.db.trackings.update_one(
                    {"_id": tracking['_id']},
                    {
                        "$set": {
                            "original_url": product_url,
                            "affiliate_url": affiliate_url,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                success += 1
                logger.info(f"✅ [{i}/{total}] Migrated: {tracking.get('product_name', 'Unknown')[:50]}")
                
                # Small delay to avoid overwhelming the database
                if i % 100 == 0:
                    await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error migrating tracking {tracking['_id']}: {e}")
                failed += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Migration Complete!")
        logger.info(f"📊 Total: {total}")
        logger.info(f"✅ Success: {success}")
        logger.info(f"❌ Failed: {failed}")
        logger.info("=" * 60)
        
        # Disconnect
        await db_manager.disconnect()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise

async def verify_migration():
    """Verify migration was successful"""
    try:
        await db_manager.connect()
        
        # Check for trackings without affiliate URLs
        missing = await db_manager.db.trackings.count_documents({
            "$or": [
                {"affiliate_url": {"$exists": False}},
                {"original_url": {"$exists": False}}
            ]
        })
        
        total = await db_manager.db.trackings.count_documents({})
        migrated = total - missing
        
        logger.info("=" * 60)
        logger.info("📊 Migration Verification")
        logger.info(f"Total trackings: {total}")
        logger.info(f"Migrated: {migrated}")
        logger.info(f"Missing affiliate URLs: {missing}")
        
        if missing == 0:
            logger.info("✅ All trackings have affiliate URLs!")
        else:
            logger.warning(f"⚠️ {missing} trackings still missing affiliate URLs")
        
        logger.info("=" * 60)
        
        await db_manager.disconnect()
        
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔄 AFFILIATE URL MIGRATION SCRIPT")
    print("=" * 60 + "\n")
    
    choice = input("Choose action:\n1. Run migration\n2. Verify migration\n3. Both\nEnter choice (1-3): ")
    
    if choice == "1":
        asyncio.run(migrate_trackings())
    elif choice == "2":
        asyncio.run(verify_migration())
    elif choice == "3":
        asyncio.run(migrate_trackings())
        asyncio.run(verify_migration())
    else:
        print("Invalid choice!")
