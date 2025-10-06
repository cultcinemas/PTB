"""
Affiliate Configuration
Store your affiliate IDs/tags for different platforms here
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Affiliate Configuration Dictionary
AFFILIATE_CONFIG = {
    'amazon': {
        'tag': os.getenv('AMAZON_AFFILIATE_TAG', 'yourtag-21'),
        'param_name': 'tag',
        'enabled': os.getenv('AMAZON_AFFILIATE_ENABLED', 'true').lower() == 'true'
    },
    'flipkart': {
        'tag': os.getenv('FLIPKART_AFFILIATE_ID', 'youraffid'),
        'param_name': 'affid',
        'enabled': os.getenv('FLIPKART_AFFILIATE_ENABLED', 'true').lower() == 'true'
    },
    'myntra': {
        'tag': os.getenv('MYNTRA_AFFILIATE_ID', 'your_myntra_id'),
        'param_name': 'affid',
        'enabled': os.getenv('MYNTRA_AFFILIATE_ENABLED', 'true').lower() == 'true'
    },
    'meesho': {
        'tag': os.getenv('MEESHO_AFFILIATE_ID', 'your_meesho_id'),
        'param_name': 'aff_id',
        'enabled': os.getenv('MEESHO_AFFILIATE_ENABLED', 'true').lower() == 'true'
    },
    'snapdeal': {
        'tag': os.getenv('SNAPDEAL_AFFILIATE_ID', 'your_snapdeal_id'),
        'param_name': 'aff_id',
        'enabled': os.getenv('SNAPDEAL_AFFILIATE_ENABLED', 'true').lower() == 'true'
    },
    'ebay': {
        'tag': os.getenv('EBAY_CAMPID', 'your_ebay_campid'),
        'param_name': 'campid',
        'enabled': os.getenv('EBAY_AFFILIATE_ENABLED', 'true').lower() == 'true'
    }
}

# Additional affiliate settings
AFFILIATE_SETTINGS = {
    'track_clicks': os.getenv('TRACK_AFFILIATE_CLICKS', 'false').lower() == 'true',
    'log_conversions': os.getenv('LOG_AFFILIATE_CONVERSIONS', 'false').lower() == 'true',
    'fallback_to_original': os.getenv('FALLBACK_TO_ORIGINAL_URL', 'true').lower() == 'true'
}


def get_affiliate_tag(platform: str) -> str:
    """
    Get affiliate tag for a platform
    
    Args:
        platform: Platform name (amazon, flipkart, etc.)
    
    Returns:
        Affiliate tag/ID
    """
    config = AFFILIATE_CONFIG.get(platform.lower())
    if config and config.get('enabled'):
        return config.get('tag', '')
    return ''


def is_affiliate_enabled(platform: str) -> bool:
    """
    Check if affiliate is enabled for a platform
    
    Args:
        platform: Platform name
    
    Returns:
        True if enabled, False otherwise
    """
    config = AFFILIATE_CONFIG.get(platform.lower())
    return config.get('enabled', False) if config else False


def get_param_name(platform: str) -> str:
    """
    Get URL parameter name for affiliate tag
    
    Args:
        platform: Platform name
    
    Returns:
        Parameter name (e.g., 'tag', 'affid')
    """
    config = AFFILIATE_CONFIG.get(platform.lower())
    return config.get('param_name', 'tag') if config else 'tag'
