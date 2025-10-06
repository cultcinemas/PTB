"""
Notification System with Affiliate Links
Sends alerts to users when price changes occur
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import db_manager
from database.models import ProductTracking

logger = logging.getLogger(__name__)


class Notifier:
    """
    Handles all user notifications with affiliate link integration
    """
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.batch_size = 30  # Telegram limit
        self.notification_queue = []
    
    async def send_price_alert(
        self,
        user_id: int,
        tracking: ProductTracking,
        old_price: float,
        new_price: float,
        change_percent: float
    ):
        """Send price change alert with affiliate link"""
        try:
            # Determine alert emoji and message
            if new_price < old_price:
                emoji = "📉"
                change_text = f"dropped by {abs(change_percent):.1f}%"
                color = "🟢"
            else:
                emoji = "📈"
                change_text = f"increased by {abs(change_percent):.1f}%"
                color = "🔴"
            
            message = (
                f"{emoji} **Price Alert!**\n\n"
                f"📦 **{tracking.product_name}**\n"
                f"🏪 Platform: {tracking.platform.title()}\n\n"
                f"💵 Old Price: ₹{old_price}\n"
                f"💵 New Price: ₹{new_price}\n"
                f"{color} Change: {change_text}\n\n"
                f"🔗 [Buy Now]({tracking.affiliate_url})\n\n"
                f"⏰ {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
            )
            
            # Create inline keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛒 View Product",
                        url=tracking.affiliate_url
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Details",
                        callback_data=f"product_details:{tracking.id}"
                    ),
                    InlineKeyboardButton(
                        text="⏸️ Pause",
                        callback_data=f"pause_tracking:{tracking.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛑 Stop Tracking",
                        callback_data=f"stop_tracking:{tracking.id}"
                    )
                ]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
            
            # Update tracking stats
            await db_manager.update_tracking(
                str(tracking.id),
                {
                    "last_alert_sent": datetime.utcnow(),
                    "alert_count": tracking.alert_count + 1
                }
            )
            
            # Update user stats
            await db_manager.db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_alerts_received": 1}}
            )
            
            logger.info(f"Price alert sent to user {user_id} for product {tracking.id}")
            
        except Exception as e:
            logger.error(f"Error sending price alert to {user_id}: {e}")
    
    async def send_stock_alert(
        self,
        user_id: int,
        tracking: ProductTracking,
        stock_status: str
    ):
        """Send stock status alert"""
        try:
            if stock_status == "in_stock":
                emoji = "✅"
                status_text = "Back in Stock!"
            else:
                emoji = "⚠️"
                status_text = "Out of Stock"
            
            message = (
                f"{emoji} **Stock Alert!**\n\n"
                f"📦 **{tracking.product_name}**\n"
                f"🏪 Platform: {tracking.platform.title()}\n\n"
                f"📊 Status: **{status_text}**\n"
                f"💵 Price: ₹{tracking.current_price}\n\n"
                f"🔗 [Check Now]({tracking.affiliate_url})"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛒 View Product",
                        url=tracking.affiliate_url
                    )
                ]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error sending stock alert: {e}")
    
    async def send_daily_summary(self, user_id: int):
        """Send daily tracking summary"""
        try:
            trackings = await db_manager.get_user_trackings(user_id, active_only=True)
            
            if not trackings:
                return
            
            # Find products with price changes in last 24 hours
            price_drops = []
            price_increases = []
            
            for tracking in trackings:
                if len(tracking.price_history) > 1:
                    latest = tracking.price_history[-1].price
                    previous = tracking.price_history[-2].price
                    
                    if latest < previous:
                        change = ((previous - latest) / previous) * 100
                        price_drops.append((tracking, change))
                    elif latest > previous:
                        change = ((latest - previous) / previous) * 100
                        price_increases.append((tracking, change))
            
            if not price_drops and not price_increases:
                # No changes to report
                return
            
            message = "📊 **Daily Summary**\n\n"
            
            if price_drops:
                message += "📉 **Price Drops:**\n"
                for tracking, change in sorted(price_drops, key=lambda x: x[1], reverse=True)[:5]:
                    message += f"• {tracking.product_name[:40]}\n"
                    message += f"  💰 ₹{tracking.current_price} (-{change:.1f}%)\n"
                    message += f"  🔗 [View]({tracking.affiliate_url})\n\n"
            
            if price_increases:
                message += "📈 **Price Increases:**\n"
                for tracking, change in sorted(price_increases, key=lambda x: x[1], reverse=True)[:5]:
                    message += f"• {tracking.product_name[:40]}\n"
                    message += f"  💰 ₹{tracking.current_price} (+{change:.1f}%)\n\n"
            
            message += f"\n📦 Total Tracked: {len(trackings)}\n"
            message += f"⏰ {datetime.now().strftime('%d %b %Y')}"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error sending daily summary to {user_id}: {e}")
    
    async def send_trending_deals(self, user_id: int, deals: List[Dict]):
        """Send trending deals notification"""
        try:
            if not deals:
                return
            
            message = "🔥 **Trending Deals in Last 24h**\n\n"
            
            for i, deal in enumerate(deals[:10], 1):
                message += (
                    f"{i}. **{deal['product_name'][:40]}**\n"
                    f"   💵 ₹{deal['current_price']} "
                    f"(📉 {deal['drop_percent']:.1f}%)\n"
                    f"   🏪 {deal['platform'].title()}\n"
                    f"   🔗 [View]({deal['affiliate_url']})\n\n"
                )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error sending trending deals: {e}")
    
    async def send_community_alert(
        self,
        user_id: int,
        shared_by_name: str,
        product_name: str,
        platform: str,
        price: float,
        affiliate_url: str,
        description: Optional[str] = None
    ):
        """Send community shared product alert"""
        try:
            message = (
                f"👥 **Community Alert**\n\n"
                f"🔔 {shared_by_name} shared a deal!\n\n"
                f"📦 **{product_name}**\n"
                f"🏪 Platform: {platform.title()}\n"
                f"💵 Price: ₹{price}\n"
            )
            
            if description:
                message += f"\n📝 {description}\n"
            
            message += f"\n🔗 [Check it out]({affiliate_url})"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛒 View Deal",
                        url=affiliate_url
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📌 Track This",
                        callback_data=f"track_shared:{affiliate_url}"
                    )
                ]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error sending community alert: {e}")
    
    async def send_batch_notifications(self, notifications: List[Dict]):
        """Send notifications in batches to respect rate limits"""
        try:
            for i in range(0, len(notifications), self.batch_size):
                batch = notifications[i:i + self.batch_size]
                
                for notification in batch:
                    try:
                        notif_type = notification.get('type')
                        user_id = notification.get('user_id')
                        
                        if notif_type == 'price_alert':
                            await self.send_price_alert(
                                user_id=user_id,
                                tracking=notification['tracking'],
                                old_price=notification['old_price'],
                                new_price=notification['new_price'],
                                change_percent=notification['change_percent']
                            )
                        elif notif_type == 'stock_alert':
                            await self.send_stock_alert(
                                user_id=user_id,
                                tracking=notification['tracking'],
                                stock_status=notification['stock_status']
                            )
                        
                        # Small delay to avoid rate limits
                        await asyncio.sleep(0.05)
                        
                    except Exception as e:
                        logger.error(f"Error sending notification to {user_id}: {e}")
                        continue
                
                # Delay between batches
                if i + self.batch_size < len(notifications):
                    await asyncio.sleep(1)
            
            logger.info(f"Sent {len(notifications)} notifications in batches")
            
        except Exception as e:
            logger.error(f"Error in batch notifications: {e}")
    
    async def send_admin_announcement(self, user_ids: List[int], message: str):
        """Send admin announcement to multiple users"""
        try:
            success_count = 0
            failed_count = 0
            
            for user_id in user_ids:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=f"📢 **Admin Announcement**\n\n{message}",
                        parse_mode="Markdown"
                    )
                    success_count += 1
                    await asyncio.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Failed to send announcement to {user_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Announcement sent: {success_count} success, {failed_count} failed")
            return {"success": success_count, "failed": failed_count}
            
        except Exception as e:
            logger.error(f"Error sending admin announcement: {e}")
            return {"success": 0, "failed": len(user_ids)}


import asyncio
