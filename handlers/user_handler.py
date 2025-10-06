"""
User handlers
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    from database.db_manager import db_manager
    
    # Create user if not exists
    user = await db_manager.get_user(message.from_user.id)
    if not user:
        await db_manager.create_user({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name
        })
    
    await message.answer(
        "👋 **Welcome to Price Tracker Bot!**\n\n"
        "I help you track product prices and get notified when they drop.\n\n"
        "**How to use:**\n"
        "1. Send me any product link\n"
        "2. I'll start tracking the price\n"
        "3. Get alerts when price changes!\n\n"
        "**Commands:**\n"
        "/track - Start tracking a product\n"
        "/my_trackings - View your tracked products\n"
        "/help - Get help",
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ **Help & Commands**\n\n"
        "**Tracking:**\n"
        "/track - Track a new product\n"
        "/my_trackings - View all tracked products\n"
        "/product <id> - View product details\n"
        "/pause <id> - Pause tracking\n"
        "/resume <id> - Resume tracking\n"
        "/stop <id> - Stop tracking\n\n"
        "**Supported Platforms:**\n"
        "• Amazon\n"
        "• Flipkart\n"
        "• Myntra\n"
        "• Meesho\n"
        "• Snapdeal\n"
        "• eBay\n\n"
        "Just send me a product link to start!",
        parse_mode="Markdown"
    )
