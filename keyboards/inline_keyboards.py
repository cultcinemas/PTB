"""
Inline keyboards for bot interactions
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_tracking_keyboard(tracking_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for tracking management"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Details",
                callback_data=f"details:{tracking_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏸️ Pause",
                callback_data=f"pause:{tracking_id}"
            ),
            InlineKeyboardButton(
                text="🛑 Stop",
                callback_data=f"stop:{tracking_id}"
            )
        ]
    ])

def get_product_actions_keyboard(tracking_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for product actions"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 View Details",
                callback_data=f"product_details:{tracking_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏸️ Pause",
                callback_data=f"pause_tracking:{tracking_id}"
            ),
            InlineKeyboardButton(
                text="🛑 Stop",
                callback_data=f"stop_tracking:{tracking_id}"
            )
        ]
    ])

def get_alert_settings_keyboard(tracking_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for alert settings"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔔 Any Change",
                callback_data=f"alert_any:{tracking_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📉 % Drop",
                callback_data=f"alert_percent:{tracking_id}"
            ),
            InlineKeyboardButton(
                text="💰 Fixed Price",
                callback_data=f"alert_fixed:{tracking_id}"
            )
        ]
    ])
