import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import BOT_TOKEN, ADMIN_IDS
from db_manager import MongoManager
from scheduler import BotScheduler
from scraper import Scraper
from notifications import send_price_alert, send_summary
from admin import is_admin, view_users, view_products, analytics_summary, send_announcement, block_user, unblock_user
from predictive import PricePredictor

# Initialize bot, dispatcher, DB, scraper, scheduler, AI
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
db = MongoManager()
scraper = Scraper()
scheduler = BotScheduler()
predictor = PricePredictor()

# ---------------- USER COMMANDS ----------------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    db.update_last_active(user_id)
    await message.answer(
        "👋 Welcome to PriceTrackerBot!\n"
        "You can track product prices from multiple platforms.\n\n"
        "Commands:\n"
        "/track <URL> - Track a new product\n"
        "/myproducts - View your tracked products\n"
        "/summary - Daily/weekly summary\n"
    )

@dp.message_handler(commands=["track"])
async def track_product(message: types.Message):
    user_id = message.from_user.id
    db.update_last_active(user_id)
    try:
        url = message.text.split(" ",1)[1]
    except IndexError:
        await message.answer("Please provide a product URL.\nUsage: /track <URL>")
        return
    
    # Scrape product details
    result = await scraper.scrape_product(url)
    if not result:
        await message.answer("Failed to fetch product details. Make sure the URL is correct.")
        return
    
    # Save product to DB
    db.products.update_one(
        {"user_id": user_id, "url": url},
        {"$set": {"name": result["name"], "price": result["price"], "platform": result["platform"], "active": True, "price_history": [{"date": datetime.utcnow(), "price": result["price"]}]}},
        upsert=True
    )
    await message.answer(f"✅ Now tracking: {result['name']} at ₹{result['price']}")

@dp.message_handler(commands=["myproducts"])
async def my_products(message: types.Message):
    user_id = message.from_user.id
    db.update_last_active(user_id)
    products = list(db.products.find({"user_id": user_id, "active": True}))
    if not products:
        await message.answer("You have no tracked products.")
        return
    msg = "📦 Your Tracked Products:\n\n"
    for p in products:
        msg += f"{p['name']} - ₹{p['price']}\nURL: {p['url']}\n\n"
    await message.answer(msg)

@dp.message_handler(commands=["summary"])
async def summary(message: types.Message):
    user_id = message.from_user.id
    await send_summary(user_id)

# ---------------- ADMIN COMMANDS ----------------

@dp.message_handler(commands=["viewusers"])
async def cmd_viewusers(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(view_users())

@dp.message_handler(commands=["viewproducts"])
async def cmd_viewproducts(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(view_products())

@dp.message_handler(commands=["analytics"])
async def cmd_analytics(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(analytics_summary())

@dp.message_handler(commands=["announce"])
async def cmd_announce(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        msg = message.text.split(" ",1)[1]
    except IndexError:
        await message.answer("Please provide announcement text.\nUsage: /announce <message>")
        return
    await send_announcement(msg)
    await message.answer("✅ Announcement sent to all users.")

@dp.message_handler(commands=["block"])
async def cmd_block(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.split(" ",1)[1])
        await message.answer(block_user(user_id))
    except:
        await message.answer("Usage: /block <user_id>")

@dp.message_handler(commands=["unblock"])
async def cmd_unblock(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.split(" ",1)[1])
        await message.answer(unblock_user(user_id))
    except:
        await message.answer("Usage: /unblock <user_id>")

# ---------------- CALLBACK HANDLERS ----------------

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("stop_"))
async def stop_tracking_callback(callback_query: types.CallbackQuery):
    url = callback_query.data.replace("stop_","")
    db.products.update_one({"url": url}, {"$set": {"active": False}})
    await bot.answer_callback_query(callback_query.id, "Tracking stopped for this product.")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("alert_"))
async def set_alert_callback(callback_query: types.CallbackQuery):
    url = callback_query.data.replace("alert_","")
    await bot.answer_callback_query(callback_query.id, "Feature coming soon: Set custom alert thresholds!")

# ---------------- BOT START ----------------

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    scheduler.start()  # Start APScheduler
    print("Bot is running...")
    executor.start_polling(dp, skip_updates=True)
