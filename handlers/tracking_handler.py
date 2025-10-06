"""
Tracking Handler with Affiliate Link Integration
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db_manager import db_manager
from utils.affiliate_manager import affiliate_manager
from scrapers.scraper_manager import scraper_manager
from keyboards.inline_keyboards import (
    get_tracking_keyboard,
    get_alert_settings_keyboard,
    get_product_actions_keyboard
)

logger = logging.getLogger(__name__)
router = Router()


class TrackingStates(StatesGroup):
    """States for tracking workflow"""
    waiting_for_url = State()
    setting_alert_type = State()
    setting_threshold = State()
    adding_notes = State()


def extract_url_from_message(text: str) -> str:
    """Extract URL from message text"""
    import re
    
    # Common URL patterns
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else text.strip()


@router.message(Command("track"))
async def cmd_track(message: Message, state: FSMContext):
    """Start tracking a product"""
    await state.set_state(TrackingStates.waiting_for_url)
    
    await message.answer(
        "🔗 **Track a Product**\n\n"
        "Send me the product link from:\n"
        "• Amazon\n"
        "• Flipkart\n"
        "• Myntra\n"
        "• Meesho\n"
        "• Snapdeal\n"
        "• eBay\n\n"
        "I'll start tracking the price for you!",
        parse_mode="Markdown"
    )


@router.message(TrackingStates.waiting_for_url)
@router.message(F.text.regexp(r'https?://'))
async def process_product_url(message: Message, state: FSMContext):
    """Process product URL and create tracking"""
    try:
        # Extract URL
        url = extract_url_from_message(message.text)
        
        # Detect platform
        platform = affiliate_manager.detect_platform(url)
        
        if not platform:
            await message.answer(
                "❌ **Unsupported Platform**\n\n"
                "Sorry, I don't support this website yet.\n"
                "Supported: Amazon, Flipkart, Myntra, Meesho, Snapdeal, eBay",
                parse_mode="Markdown"
            )
            return
        
        # Send processing message
        processing_msg = await message.answer(
            "⏳ **Processing...**\n"
            f"Platform: {platform.title()}\n"
            "Fetching product details...",
            parse_mode="Markdown"
        )
        
        # Convert to affiliate link
        affiliate_url = affiliate_manager.convert_to_affiliate(url, platform)
        
        logger.info(f"Original URL: {url}")
        logger.info(f"Affiliate URL: {affiliate_url}")
        
        # Scrape product details
        product_data = await scraper_manager.scrape_product(url, platform)
        
        if not product_data or 'error' in product_data:
            await processing_msg.edit_text(
                "❌ **Failed to fetch product**\n\n"
                f"Error: {product_data.get('error', 'Unknown error')}\n"
                "Please check the URL and try again.",
                parse_mode="Markdown"
            )
            await state.clear()
            return
        
        # Check if user exists, create if not
        user = await db_manager.get_user(message.from_user.id)
        if not user:
            user = await db_manager.create_user({
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name
            })
        
        # Check tracking limit (premium users get more)
        user_trackings = await db_manager.get_user_trackings(message.from_user.id)
        max_trackings = 50 if user.is_premium else 10
        
        if len(user_trackings) >= max_trackings:
            await processing_msg.edit_text(
                f"⚠️ **Tracking Limit Reached**\n\n"
                f"You can track up to {max_trackings} products.\n"
                f"Current: {len(user_trackings)}\n\n"
                "Stop tracking some products or upgrade to Premium for more!",
                parse_mode="Markdown"
            )
            await state.clear()
            return
        
        # Create tracking entry
        tracking_data = {
            "user_id": message.from_user.id,
            "product_url": url,
            "original_url": url,  # Store original
            "affiliate_url": affiliate_url,  # Store affiliate version
            "platform": platform,
            "product_name": product_data.get('name'),
            "current_price": product_data.get('price'),
            "original_price": product_data.get('original_price', product_data.get('price')),
            "currency": product_data.get('currency', 'INR'),
            "image_url": product_data.get('image_url'),
            "product_id": product_data.get('product_id'),
            "price_history": [{
                "price": product_data.get('price'),
                "currency": product_data.get('currency', 'INR'),
                "timestamp": datetime.utcnow(),
                "stock_status": product_data.get('stock_status', 'in_stock'),
                "discount": product_data.get('discount')
            }]
        }
        
        tracking = await db_manager.add_tracking(tracking_data)
        
        # Success message with affiliate link
        discount_text = f"\n💰 Discount: {product_data.get('discount', 0)}%" if product_data.get('discount') else ""
        
        await processing_msg.edit_text(
            f"✅ **Now Tracking!**\n\n"
            f"📦 **{product_data.get('name', 'Product')}**\n"
            f"🏪 Platform: {platform.title()}\n"
            f"💵 Current Price: ₹{product_data.get('price', 'N/A')}"
            f"{discount_text}\n\n"
            f"🔗 [View Product]({affiliate_url})\n\n"
            f"🔔 You'll be notified of any price changes!\n"
            f"🆔 Tracking ID: `{str(tracking.id)}`",
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_product_actions_keyboard(str(tracking.id))
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing product URL: {e}", exc_info=True)
        await message.answer(
            "❌ **An error occurred**\n\n"
            "Please try again or contact support.",
            parse_mode="Markdown"
        )
        await state.clear()


@router.message(Command("my_trackings"))
async def cmd_my_trackings(message: Message):
    """Show user's tracked products"""
    try:
        trackings = await db_manager.get_user_trackings(message.from_user.id)
        
        if not trackings:
            await message.answer(
                "📭 **No Tracked Products**\n\n"
                "You haven't tracked any products yet.\n"
                "Send me a product link to start tracking!",
                parse_mode="Markdown"
            )
            return
        
        response = f"📊 **Your Tracked Products** ({len(trackings)})\n\n"
        
        for i, tracking in enumerate(trackings, 1):
            status_emoji = "⏸️" if tracking.is_paused else "✅"
            platform_emoji = {
                "amazon": "📦",
                "flipkart": "🛒",
                "myntra": "👗",
                "meesho": "🛍️",
                "snapdeal": "🎁",
                "ebay": "🏪"
            }.get(tracking.platform, "🔗")
            
            price_change = ""
            if tracking.price_history and len(tracking.price_history) > 1:
                old_price = tracking.price_history[0].price
                new_price = tracking.current_price
                if new_price < old_price:
                    diff = ((old_price - new_price) / old_price) * 100
                    price_change = f" 📉 -{diff:.1f}%"
                elif new_price > old_price:
                    diff = ((new_price - old_price) / old_price) * 100
                    price_change = f" 📈 +{diff:.1f}%"
            
            response += (
                f"{status_emoji} **{i}. {tracking.product_name[:50]}**\n"
                f"{platform_emoji} {tracking.platform.title()} | "
                f"💵 ₹{tracking.current_price}{price_change}\n"
                f"🔗 [View Product]({tracking.affiliate_url})\n"
                f"🆔 ID: `{str(tracking.id)}`\n\n"
            )
        
        response += "💡 Use /product <id> for details\n"
        response += "⏸️ Use /pause <id> to pause tracking\n"
        response += "🛑 Use /stop <id> to stop tracking"
        
        await message.answer(
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error showing trackings: {e}", exc_info=True)
        await message.answer(
            "❌ An error occurred while fetching your trackings.",
            parse_mode="Markdown"
        )


@router.message(Command("product"))
async def cmd_product_details(message: Message):
    """Show detailed product information"""
    try:
        # Extract tracking ID from command
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ **Invalid Command**\n\n"
                "Usage: /product <tracking_id>\n"
                "Get tracking ID from /my_trackings",
                parse_mode="Markdown"
            )
            return
        
        tracking_id = parts[1].strip()
        tracking = await db_manager.get_tracking_by_id(tracking_id)
        
        if not tracking or tracking.user_id != message.from_user.id:
            await message.answer(
                "❌ **Product Not Found**\n\n"
                "This tracking ID doesn't exist or doesn't belong to you.",
                parse_mode="Markdown"
            )
            return
        
        # Calculate statistics
        price_history = tracking.price_history
        lowest_price = min([p.price for p in price_history]) if price_history else tracking.current_price
        highest_price = max([p.price for p in price_history]) if price_history else tracking.current_price
        
        price_change = 0
        if len(price_history) > 1:
            original = price_history[0].price
            current = tracking.current_price
            price_change = ((current - original) / original) * 100
        
        status = "✅ Active" if tracking.is_active and not tracking.is_paused else "⏸️ Paused" if tracking.is_paused else "🛑 Stopped"
        
        response = (
            f"📦 **Product Details**\n\n"
            f"**Name:** {tracking.product_name}\n"
            f"**Platform:** {tracking.platform.title()}\n"
            f"**Status:** {status}\n\n"
            f"💵 **Current Price:** ₹{tracking.current_price}\n"
            f"📊 **Original Price:** ₹{tracking.original_price}\n"
            f"📉 **Lowest Price:** ₹{lowest_price}\n"
            f"📈 **Highest Price:** ₹{highest_price}\n"
            f"📊 **Price Change:** {price_change:+.2f}%\n\n"
            f"📅 **Tracked Since:** {tracking.created_at.strftime('%d %b %Y')}\n"
            f"🔍 **Checks:** {tracking.check_count}\n"
            f"🔔 **Alerts Sent:** {tracking.alert_count}\n\n"
            f"🔗 [View Product]({tracking.affiliate_url})\n\n"
            f"🆔 **ID:** `{str(tracking.id)}`"
        )
        
        if tracking.notes:
            response += f"\n\n📝 **Notes:** {tracking.notes}"
        
        if tracking.tags:
            response += f"\n🏷️ **Tags:** {', '.join(tracking.tags)}"
        
        await message.answer(
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_product_actions_keyboard(tracking_id)
        )
        
    except Exception as e:
        logger.error(f"Error showing product details: {e}", exc_info=True)
        await message.answer(
            "❌ An error occurred while fetching product details.",
            parse_mode="Markdown"
        )


@router.message(Command("pause"))
async def cmd_pause_tracking(message: Message):
    """Pause product tracking"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ Usage: /pause <tracking_id>",
                parse_mode="Markdown"
            )
            return
        
        tracking_id = parts[1].strip()
        tracking = await db_manager.get_tracking_by_id(tracking_id)
        
        if not tracking or tracking.user_id != message.from_user.id:
            await message.answer("❌ Product not found.", parse_mode="Markdown")
            return
        
        await db_manager.pause_tracking(tracking_id)
        
        await message.answer(
            f"⏸️ **Tracking Paused**\n\n"
            f"Product: {tracking.product_name}\n"
            f"Use /resume {tracking_id} to resume tracking.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error pausing tracking: {e}")
        await message.answer("❌ An error occurred.", parse_mode="Markdown")


@router.message(Command("resume"))
async def cmd_resume_tracking(message: Message):
    """Resume product tracking"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ Usage: /resume <tracking_id>",
                parse_mode="Markdown"
            )
            return
        
        tracking_id = parts[1].strip()
        tracking = await db_manager.get_tracking_by_id(tracking_id)
        
        if not tracking or tracking.user_id != message.from_user.id:
            await message.answer("❌ Product not found.", parse_mode="Markdown")
            return
        
        await db_manager.resume_tracking(tracking_id)
        
        await message.answer(
            f"✅ **Tracking Resumed**\n\n"
            f"Product: {tracking.product_name}\n"
            f"I'll continue monitoring price changes.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error resuming tracking: {e}")
        await message.answer("❌ An error occurred.", parse_mode="Markdown")


@router.message(Command("stop"))
async def cmd_stop_tracking(message: Message):
    """Stop product tracking"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ Usage: /stop <tracking_id>",
                parse_mode="Markdown"
            )
            return
        
        tracking_id = parts[1].strip()
        tracking = await db_manager.get_tracking_by_id(tracking_id)
        
        if not tracking or tracking.user_id != message.from_user.id:
            await message.answer("❌ Product not found.", parse_mode="Markdown")
            return
        
        await db_manager.stop_tracking(tracking_id, message.from_user.id)
        
        await message.answer(
            f"🛑 **Tracking Stopped**\n\n"
            f"Product: {tracking.product_name}\n"
            f"This product has been removed from your tracking list.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error stopping tracking: {e}")
        await message.answer("❌ An error occurred.", parse_mode="Markdown")
