"""
Database Models for Price Tracker Bot
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId validator for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class PriceHistory(BaseModel):
    """Price history entry"""
    price: float
    currency: str = "INR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stock_status: str = "in_stock"
    discount: Optional[float] = None


class AlertSettings(BaseModel):
    """Alert configuration for a tracked product"""
    alert_type: str = "any_change"  # any_change, percentage_drop, fixed_price, stock_alert
    threshold: Optional[float] = None  # For percentage/fixed price alerts
    enabled: bool = True
    notify_on_stock: bool = True
    notify_on_price_increase: bool = False


class ProductTracking(BaseModel):
    """Product tracking model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: int
    product_url: str
    original_url: str  # Store original URL
    affiliate_url: str  # Store affiliate URL
    platform: str
    product_name: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    currency: str = "INR"
    image_url: Optional[str] = None
    product_id: Optional[str] = None
    
    # Tracking settings
    alert_settings: AlertSettings = Field(default_factory=AlertSettings)
    is_active: bool = True
    is_paused: bool = False
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Price history
    price_history: List[PriceHistory] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    last_alert_sent: Optional[datetime] = None
    
    # Stats
    check_count: int = 0
    alert_count: int = 0
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class User(BaseModel):
    """User model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Preferences
    language: str = "en"
    timezone: str = "UTC"
    notification_time: Optional[str] = None  # For daily summaries
    
    # Subscription
    is_premium: bool = False
    subscription_expires: Optional[datetime] = None
    
    # Settings
    daily_summary: bool = False
    weekly_summary: bool = False
    trending_deals: bool = True
    
    # Status
    is_active: bool = True
    is_blocked: bool = False
    
    # Stats
    total_trackings: int = 0
    active_trackings: int = 0
    total_alerts_received: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class CommunityAlert(BaseModel):
    """Community shared product alert"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    shared_by: int
    product_url: str
    affiliate_url: str  # Affiliate link
    product_name: str
    platform: str
    current_price: float
    discount: Optional[float] = None
    description: Optional[str] = None
    shared_with: List[int] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class AdminAnnouncement(BaseModel):
    """Admin announcement model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    message: str
    target_users: str = "all"  # all, premium, active
    sent_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class BotHealth(BaseModel):
    """Bot health monitoring"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    scheduler_status: str = "running"
    scraper_status: str = "running"
    db_status: str = "connected"
    redis_status: str = "connected"
    
    active_jobs: int = 0
    failed_jobs: int = 0
    
    last_scrape: Optional[datetime] = None
    last_alert_batch: Optional[datetime] = None
    
    uptime_start: datetime = Field(default_factory=datetime.utcnow)
    last_check: datetime = Field(default_factory=datetime.utcnow)
    
    errors: List[Dict] = Field(default_factory=list)
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class Analytics(BaseModel):
    """Analytics data"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    date: datetime = Field(default_factory=datetime.utcnow)
    
    total_users: int = 0
    active_users: int = 0
    premium_users: int = 0
    
    total_trackings: int = 0
    active_trackings: int = 0
    
    alerts_sent: int = 0
    scrapes_performed: int = 0
    
    top_platforms: Dict[str, int] = Field(default_factory=dict)
    top_products: List[Dict] = Field(default_factory=list)
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
