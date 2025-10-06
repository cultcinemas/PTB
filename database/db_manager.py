"""
Database Manager with Multi-MongoDB Support and Affiliate URL Handling
"""
import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from database.models import (
    ProductTracking, User, CommunityAlert, 
    AdminAnnouncement, BotHealth, Analytics
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MongoDB connections with failover support
    """
    
    def __init__(self):
        self.primary_uri = os.getenv("MONGODB_URI")
        self.secondary_uri = os.getenv("MONGODB_URI_SECONDARY", None)
        
        self.primary_client: Optional[AsyncIOMotorClient] = None
        self.secondary_client: Optional[AsyncIOMotorClient] = None
        
        self.current_client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.db_name = os.getenv("DB_NAME", "price_tracker_bot")
        
        self.is_connected = False
    
    async def connect(self):
        """Connect to MongoDB with failover support"""
        try:
            # Try primary connection
            self.primary_client = AsyncIOMotorClient(
                self.primary_uri,
                serverSelectionTimeoutMS=5000
            )
            await self.primary_client.admin.command('ping')
            
            self.current_client = self.primary_client
            self.db = self.current_client[self.db_name]
            self.is_connected = True
            
            logger.info("✅ Connected to primary MongoDB")
            
            # Try secondary connection if available
            if self.secondary_uri:
                try:
                    self.secondary_client = AsyncIOMotorClient(
                        self.secondary_uri,
                        serverSelectionTimeoutMS=5000
                    )
                    await self.secondary_client.admin.command('ping')
                    logger.info("✅ Secondary MongoDB connection available")
                except Exception as e:
                    logger.warning(f"Secondary MongoDB unavailable: {e}")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ Primary MongoDB connection failed: {e}")
            
            # Try secondary if available
            if self.secondary_uri:
                try:
                    self.secondary_client = AsyncIOMotorClient(
                        self.secondary_uri,
                        serverSelectionTimeoutMS=5000
                    )
                    await self.secondary_client.admin.command('ping')
                    
                    self.current_client = self.secondary_client
                    self.db = self.current_client[self.db_name]
                    self.is_connected = True
                    
                    logger.info("✅ Connected to secondary MongoDB")
                    await self._create_indexes()
                    
                except Exception as e2:
                    logger.error(f"❌ Secondary MongoDB also failed: {e2}")
                    raise Exception("Failed to connect to any MongoDB instance")
            else:
                raise e
    
    async def _create_indexes(self):
        """Create necessary indexes"""
        try:
            # Users collection
            await self.db.users.create_index("user_id", unique=True)
            await self.db.users.create_index("is_active")
            await self.db.users.create_index("is_premium")
            
            # Product trackings collection
            await self.db.trackings.create_index("user_id")
            await self.db.trackings.create_index("product_url")
            await self.db.trackings.create_index("platform")
            await self.db.trackings.create_index("is_active")
            await self.db.trackings.create_index("is_paused")
            await self.db.trackings.create_index([("user_id", 1), ("is_active", 1)])
            await self.db.trackings.create_index("last_checked")
            await self.db.trackings.create_index("created_at")
            
            # Community alerts
            await self.db.community_alerts.create_index("shared_by")
            await self.db.community_alerts.create_index("created_at")
            await self.db.community_alerts.create_index("expires_at")
            
            # Analytics
            await self.db.analytics.create_index("date")
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def disconnect(self):
        """Close database connections"""
        if self.primary_client:
            self.primary_client.close()
        if self.secondary_client:
            self.secondary_client.close()
        
        self.is_connected = False
        logger.info("Disconnected from MongoDB")
    
    # User operations
    async def create_user(self, user_data: Dict) -> User:
        """Create a new user"""
        user = User(**user_data)
        result = await self.db.users.insert_one(user.model_dump(by_alias=True, exclude=['id']))
        user.id = result.inserted_id
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by Telegram user ID"""
        user_data = await self.db.users.find_one({"user_id": user_id})
        return User(**user_data) if user_data else None
    
    async def update_user(self, user_id: int, update_data: Dict):
        """Update user data"""
        update_data['updated_at'] = datetime.utcnow()
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    # Product tracking operations
    async def add_tracking(self, tracking_data: Dict) -> ProductTracking:
        """Add a new product tracking with affiliate URL"""
        tracking = ProductTracking(**tracking_data)
        result = await self.db.trackings.insert_one(
            tracking.model_dump(by_alias=True, exclude=['id'])
        )
        tracking.id = result.inserted_id
        
        # Update user stats
        await self.db.users.update_one(
            {"user_id": tracking_data['user_id']},
            {
                "$inc": {"total_trackings": 1, "active_trackings": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return tracking
    
    async def get_user_trackings(
        self, 
        user_id: int, 
        active_only: bool = True,
        include_paused: bool = False
    ) -> List[ProductTracking]:
        """Get all trackings for a user"""
        query = {"user_id": user_id}
        
        if active_only:
            query["is_active"] = True
            
        if not include_paused:
            query["is_paused"] = False
        
        trackings = await self.db.trackings.find(query).to_list(length=None)
        return [ProductTracking(**t) for t in trackings]
    
    async def get_tracking_by_id(self, tracking_id: str) -> Optional[ProductTracking]:
        """Get tracking by ID"""
        from bson import ObjectId
        tracking_data = await self.db.trackings.find_one({"_id": ObjectId(tracking_id)})
        return ProductTracking(**tracking_data) if tracking_data else None
    
    async def update_tracking(self, tracking_id: str, update_data: Dict):
        """Update tracking data"""
        from bson import ObjectId
        update_data['updated_at'] = datetime.utcnow()
        
        await self.db.trackings.update_one(
            {"_id": ObjectId(tracking_id)},
            {"$set": update_data}
        )
    
    async def update_tracking_price(
        self, 
        tracking_id: str, 
        new_price: float,
        stock_status: str = "in_stock",
        discount: Optional[float] = None
    ):
        """Update product price and add to history"""
        from bson import ObjectId
        
        price_entry = {
            "price": new_price,
            "currency": "INR",
            "timestamp": datetime.utcnow(),
            "stock_status": stock_status,
            "discount": discount
        }
        
        await self.db.trackings.update_one(
            {"_id": ObjectId(tracking_id)},
            {
                "$set": {
                    "current_price": new_price,
                    "updated_at": datetime.utcnow(),
                    "last_checked": datetime.utcnow()
                },
                "$push": {"price_history": price_entry},
                "$inc": {"check_count": 1}
            }
        )
    
    async def pause_tracking(self, tracking_id: str):
        """Pause a tracking"""
        await self.update_tracking(tracking_id, {"is_paused": True})
    
    async def resume_tracking(self, tracking_id: str):
        """Resume a tracking"""
        await self.update_tracking(tracking_id, {"is_paused": False})
    
    async def stop_tracking(self, tracking_id: str, user_id: int):
        """Stop tracking a product"""
        await self.update_tracking(tracking_id, {"is_active": False})
        
        # Update user stats
        await self.db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"active_trackings": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    async def get_all_active_trackings(self) -> List[ProductTracking]:
        """Get all active trackings for scheduled scraping"""
        trackings = await self.db.trackings.find({
            "is_active": True,
            "is_paused": False
        }).to_list(length=None)
        
        return [ProductTracking(**t) for t in trackings]
    
    async def get_trackings_to_check(self, limit: int = 100) -> List[ProductTracking]:
        """Get trackings that need to be checked (oldest first)"""
        trackings = await self.db.trackings.find({
            "is_active": True,
            "is_paused": False
        }).sort("last_checked", 1).limit(limit).to_list(length=limit)
        
        return [ProductTracking(**t) for t in trackings]
    
    # Community alerts
    async def create_community_alert(self, alert_data: Dict) -> CommunityAlert:
        """Create a community alert"""
        alert = CommunityAlert(**alert_data)
        result = await self.db.community_alerts.insert_one(
            alert.model_dump(by_alias=True, exclude=['id'])
        )
        alert.id = result.inserted_id
        return alert
    
    async def get_community_alerts(self, user_id: int) -> List[CommunityAlert]:
        """Get community alerts for a user"""
        alerts = await self.db.community_alerts.find({
            "shared_with": user_id,
            "expires_at": {"$gt": datetime.utcnow()}
        }).to_list(length=None)
        
        return [CommunityAlert(**a) for a in alerts]
    
    # Analytics
    async def record_analytics(self, analytics_data: Dict):
        """Record daily analytics"""
        analytics = Analytics(**analytics_data)
        await self.db.analytics.insert_one(
            analytics.model_dump(by_alias=True, exclude=['id'])
        )
    
    async def get_analytics(self, days: int = 7) -> List[Analytics]:
        """Get analytics for last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        analytics = await self.db.analytics.find({
            "date": {"$gte": start_date}
        }).sort("date", -1).to_list(length=None)
        
        return [Analytics(**a) for a in analytics]
    
    # Cleanup operations
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old inactive data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old inactive trackings
        result = await self.db.trackings.delete_many({
            "is_active": False,
            "updated_at": {"$lt": cutoff_date}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} old trackings")
        
        # Delete expired community alerts
        result = await self.db.community_alerts.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} expired community alerts")
    
    async def get_stats(self) -> Dict:
        """Get overall bot statistics"""
        total_users = await self.db.users.count_documents({})
        active_users = await self.db.users.count_documents({"is_active": True})
        premium_users = await self.db.users.count_documents({"is_premium": True})
        
        total_trackings = await self.db.trackings.count_documents({})
        active_trackings = await self.db.trackings.count_documents({
            "is_active": True,
            "is_paused": False
        })
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "premium_users": premium_users,
            "total_trackings": total_trackings,
            "active_trackings": active_trackings
        }

# Global instance
db_manager = DatabaseManager()
