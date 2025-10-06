#!/usr/bin/env python3
"""
Test script to validate bot functionality
Run this before deployment to ensure everything works
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_imports():
    """Test all imports work correctly"""
    logger.info("Testing imports...")
    
    try:
        # Test core imports
        from database.db_manager import db_manager
        from database.models import ProductTracking, User
        from scrapers.scraper_manager import scraper_manager
        from utils.affiliate_manager import affiliate_manager
        from config.affiliate_config import AFFILIATE_CONFIG
        from notifications.notifier import Notifier
        from keyboards.inline_keyboards import get_tracking_keyboard
        
        # Test handlers
        from handlers import tracking_handler, admin_handler, user_handler
        
        logger.info("✅ All imports successful")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during import: {e}")
        return False

async def test_affiliate_manager():
    """Test affiliate manager functionality"""
    logger.info("Testing affiliate manager...")
    
    try:
        # Test URL detection
        amazon_url = "https://www.amazon.in/dp/B08N5WRWNW"
        flipkart_url = "https://www.flipkart.com/product/p/itmexample"
        
        platform = affiliate_manager.detect_platform(amazon_url)
        if platform != "amazon":
            logger.error(f"❌ Failed to detect Amazon platform: got {platform}")
            return False
        
        platform = affiliate_manager.detect_platform(flipkart_url)
        if platform != "flipkart":
            logger.error(f"❌ Failed to detect Flipkart platform: got {platform}")
            return False
        
        # Test affiliate conversion (with dummy URLs)
        affiliate_url = affiliate_manager.convert_to_affiliate(amazon_url, "amazon")
        if not affiliate_url:
            logger.error("❌ Failed to convert Amazon URL")
            return False
        
        logger.info("✅ Affiliate manager tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Affiliate manager test failed: {e}")
        return False

async def test_scraper_basic():
    """Test basic scraper functionality"""
    logger.info("Testing scraper manager...")
    
    try:
        # Test with a simple URL (won't actually scrape, just test structure)
        test_url = "https://www.example.com/product"
        
        # Test that scraper methods exist and return proper format
        result = await scraper_manager._generic_scrape(test_url, "test")
        
        # Should return error but with proper structure
        if not isinstance(result, dict):
            logger.error("❌ Scraper should return dict")
            return False
        
        if "error" not in result and "name" not in result:
            logger.error("❌ Scraper should return either error or product data")
            return False
        
        logger.info("✅ Scraper manager basic tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Scraper test failed: {e}")
        return False

async def test_database_models():
    """Test database models"""
    logger.info("Testing database models...")
    
    try:
        # Test ProductTracking model
        tracking_data = {
            "user_id": 123456789,
            "product_url": "https://example.com/product",
            "original_url": "https://example.com/product",
            "affiliate_url": "https://example.com/product?tag=test",
            "platform": "amazon",
            "product_name": "Test Product",
            "current_price": 1000.0,
            "currency": "INR"
        }
        
        tracking = ProductTracking(**tracking_data)
        if not tracking:
            logger.error("❌ Failed to create ProductTracking model")
            return False
        
        # Test User model
        user_data = {
            "user_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
        
        user = User(**user_data)
        if not user:
            logger.error("❌ Failed to create User model")
            return False
        
        logger.info("✅ Database models tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database models test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    logger.info("🚀 Starting bot validation tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Affiliate Manager", test_affiliate_manager),
        ("Scraper Manager", test_scraper_basic),
        ("Database Models", test_database_models)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if await test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with exception: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Bot is ready for deployment.")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check critical environment variables
    if not os.getenv("BOT_TOKEN"):
        logger.error("❌ BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    if not os.getenv("MONGODB_URI"):
        logger.error("❌ MONGODB_URI not found in environment variables")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
