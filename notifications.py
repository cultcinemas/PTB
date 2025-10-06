from aiogram import Bot, types
from config import BOT_TOKEN, NOTIFICATION_BATCH_SIZE
from helpers import format_price_alert, generate_price_chart
from db_manager import MongoManager
import asyncio

bot = Bot(token=BOT_TOKEN)
db = MongoManager()

# Send price alert for a single product
async def send_price_alert(user_id, product, old_price, new_price):
    message = format_price_alert(product, old_price, new_price)
    try:
        # Inline buttons: View Product, Stop Tracking, Set Alert
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("View Product", url=product["url"]))
        keyboard.add(types.InlineKeyboardButton("Stop Tracking", callback_data=f"stop_{product['url']}"))
        keyboard.add(types.InlineKeyboardButton("Set Alert", callback_data=f"alert_{product['url']}"))
        await bot.send_message(user_id, message, reply_markup=keyboard)
    except Exception as e:
        print(f"Error sending alert to {user_id}: {e}")

# Send trending deals (top N products)
async def send_trending_deals(user_id, trending_products):
    if not trending_products:
        return
    messages = []
    for p in trending_products:
        msg = f"{p['name']} - ₹{p['price']} ({p.get('price_change', 0)} change)\n{p['url']}"
        messages.append(msg)
    message = "🔥 Trending Deals (24h):\n\n" + "\n\n".join(messages[:NOTIFICATION_BATCH_SIZE])
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        print(f"Error sending trending deals to {user_id}: {e}")

# Batch notifications for multiple users/products
async def batch_price_alerts(alert_list):
    tasks = []
    for alert in alert_list:
        tasks.append(send_price_alert(alert["user_id"], alert["product"], alert["old_price"], alert["new_price"]))
    await asyncio.gather(*tasks)

# Daily/weekly summary
async def send_summary(user_id):
    # Get all products for user
    products = list(db.products.find({"user_id": user_id}))
    if not products:
        return
    messages = []
    for p in products:
        messages.append(f"{p['name']}: ₹{p['price']}")
    message = "📊 Your tracked products summary:\n\n" + "\n".join(messages)
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        print(f"Error sending summary to {user_id}: {e}")
