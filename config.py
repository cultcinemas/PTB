import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# MongoDB URIs (support multi-DB)
MONGO_URIS = os.getenv("MONGO_URIS", "").split(",")  # comma-separated URIs
DB_NAME = os.getenv("DB_NAME", "PriceTrackerDB")

# Scheduler & notification settings
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", 30))  # in minutes
NOTIFICATION_BATCH_SIZE = int(os.getenv("NOTIFICATION_BATCH_SIZE", 10))

# Auto-delete inactive users
INACTIVITY_DAYS = int(os.getenv("INACTIVITY_DAYS", 90))

# Supported Platforms
PLATFORMS = ["amazon", "flipkart", "myntra", "meesho", "snapdeal", "ebay"]

# AI / Predictive
PREDICTIVE_MODEL_PATH = os.getenv("PREDICTIVE_MODEL_PATH", "models/price_predictor.pkl")

# Logging
LOG_FILE = os.getenv("LOG_FILE", "bot.log")
