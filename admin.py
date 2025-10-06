from aiogram import types
from db_manager import MongoManager
from notifications import send_trending_deals, send_price_alert
from datetime import datetime, timedelta
from helpers import format_price_alert
import matplotlib.pyplot as plt
import io

db = MongoManager()

ADMIN_IDS = [123456789]  # Replace with your Telegram ID(s)

# Check if user is admin
def is_admin(user_id):
    return user_id in ADMIN_IDS

# View all users
def view_users():
    users = list(db.users.find())
    user_list = []
    for u in users:
        user_list.append(f"UserID: {u['user_id']} | Products: {db.products.count_documents({'user_id': u['user_id']})} | Last Active: {u.get('last_active')}")
    return "\n".join(user_list)

# Block / suspend user
def block_user(user_id):
    db.users.update_one({"user_id": user_id}, {"$set": {"blocked": True}})
    return f"User {user_id} blocked."

def unblock_user(user_id):
    db.users.update_one({"user_id": user_id}, {"$set": {"blocked": False}})
    return f"User {user_id} unblocked."

# View all tracked products
def view_products():
    products = list(db.products.find())
    product_list = []
    for p in products:
        product_list.append(f"{p['name']} | UserID: {p['user_id']} | Price: ₹{p['price']} | URL: {p['url']}")
    return "\n".join(product_list)

# Remove duplicate products
def remove_duplicates():
    urls_seen = set()
    duplicates = []
    products = list(db.products.find())
    for p in products:
        if p['url'] in urls_seen:
            db.products.delete_one({"_id": p["_id"]})
            duplicates.append(p['url'])
        else:
            urls_seen.add(p['url'])
    return duplicates

# Blacklist domains
def blacklist_domain(domain):
    db.db["blacklist"].update_one({"domain": domain}, {"$set": {"domain": domain}}, upsert=True)
    return f"Domain '{domain}' blacklisted."

# Analytics & reporting
def analytics_summary():
    total_users = db.users.count_documents({})
    active_users = db.users.count_documents({"blocked": {"$ne": True}})
    total_products = db.products.count_documents({})
    alerts_sent = db.alerts.count_documents({})
    return (
        f"📊 Analytics Summary:\n"
        f"Total Users: {total_users}\n"
        f"Active Users: {active_users}\n"
        f"Total Products Tracked: {total_products}\n"
        f"Total Alerts Sent: {alerts_sent}"
    )

# Generate product price history chart for admin
def generate_admin_chart(product_id):
    product = db.products.find_one({"_id": product_id})
    if not product or "price_history" not in product:
        return None
    dates = [ph["date"] for ph in product["price_history"]]
    prices = [ph["price"] for ph in product["price_history"]]
    plt.figure(figsize=(6,3))
    plt.plot(dates, prices, marker='o')
    plt.title(f"Price History: {product['name']}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_bytes = buf.read()
    buf.close()
    return img_bytes

# Bulk notification / announcement
async def send_announcement(message):
    users = db.users.find({"blocked": {"$ne": True}})
    from notifications import bot
    for u in users:
        try:
            await bot.send_message(u["user_id"], message)
        except Exception as e:
            print(f"Error sending announcement to {u['user_id']}: {e}")
