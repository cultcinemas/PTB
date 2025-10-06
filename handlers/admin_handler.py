"""
Admin handlers
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import os

router = Router()

ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👑 **Admin Panel**\n\n"
        "/stats - Bot statistics\n"
        "/announce - Send announcement\n"
        "/users - User management",
        parse_mode="Markdown"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    from database.db_manager import db_manager
    stats = await db_manager.get_stats()
    
    await message.answer(
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"✅ Active Users: {stats['active_users']}\n"
        f"⭐ Premium Users: {stats['premium_users']}\n"
        f"📦 Total Trackings: {stats['total_trackings']}\n"
        f"🔔 Active Trackings: {stats['active_trackings']}",
        parse_mode="Markdown"
    )
