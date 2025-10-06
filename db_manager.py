from pymongo import MongoClient
from datetime import datetime, timedelta
from config import MONGO_URIS, DB_NAME, INACTIVITY_DAYS
import random

class MongoManager:
    def __init__(self):
        # Choose a random URI for failover/load-balancing
        uri = random.choice(MONGO_URIS)
        self.client = MongoClient(uri)
        self.db = self.client[DB_NAME]
        self.users = self.db["users"]
        self.products = self.db["products"]
        self.alerts = self.db["alerts"]

    # User activity tracking
    def update_last_active(self, user_id):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.utcnow()}},
            upsert=True
        )

    # Auto-delete inactive users
    def cleanup_inactive_users(self):
        threshold = datetime.utcnow() - timedelta(days=INACTIVITY_DAYS)
        inactive_users = self.users.find({"last_active": {"$lt": threshold}})
        for user in inactive_users:
            uid = user["user_id"]
            self.products.delete_many({"user_id": uid})
            self.alerts.delete_many({"user_id": uid})
            self.users.delete_one({"user_id": uid})
        return len(list(inactive_users))  # Number of deleted users
