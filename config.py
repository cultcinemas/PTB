import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Telegram Bot
BOT_TOKEN = os.getenv("7386512270:AAHXGm634MpDeP1EtR_qMW7fea69a9W_zJE")

# MongoDB URIs (support multi-DB)
MONGO_URIS = os.getenv("MONGO_URIS", "mongodb+srv://pinkybitlu:pinky7268@cluster0.dizew5m.mongodb.net/?retryWrites=true&w=majority").split(",")  # comma-separated URIs
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
