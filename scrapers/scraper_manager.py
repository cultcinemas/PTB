"""
Scraper Manager - handles product scraping
"""
import logging
import asyncio
import re
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ScraperManager:
    """Manages product scraping across platforms"""
    
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300, use_dns_cache=True)
            self.session = aiohttp.ClientSession(headers=headers, connector=connector)
        return self.session
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_product(self, url: str, platform: str) -> Optional[Dict]:
        """
        Scrape product details from URL
        
        Returns dict with:
        - name: Product name
        - price: Current price
        - original_price: Original/MRP price
        - currency: Currency code
        - image_url: Product image URL
        - stock_status: in_stock/out_of_stock
        - discount: Discount percentage
        - product_id: Platform product ID
        """
        try:
            logger.info(f"Scraping {platform} product: {url}")
            
            if platform == 'amazon':
                return await self._scrape_amazon(url)
            elif platform == 'flipkart':
                return await self._scrape_flipkart(url)
            elif platform == 'myntra':
                return await self._scrape_myntra(url)
            elif platform == 'meesho':
                return await self._scrape_meesho(url)
            elif platform == 'snapdeal':
                return await self._scrape_snapdeal(url)
            elif platform == 'ebay':
                return await self._scrape_ebay(url)
            else:
                return {"error": f"Platform {platform} not supported"}
            
        except Exception as e:
            logger.error(f"Scraping error for {platform}: {e}", exc_info=True)
            return {"error": str(e)}
    
    def extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        if not price_text:
            return 0.0
        
        # Remove currency symbols and commas
        price_clean = re.sub(r'[₹$,\s]', '', price_text)
        
        # Extract first number found
        price_match = re.search(r'[\d,]+(?:\.\d+)?', price_clean)
        if price_match:
            return float(price_match.group().replace(',', ''))
        return 0.0
    
    def extract_product_id(self, url: str, platform: str) -> str:
        """Extract product ID from URL"""
        try:
            if platform == 'amazon':
                # Amazon ASIN extraction
                match = re.search(r'/(?:dp|product)/([A-Z0-9]{10})', url)
                return match.group(1) if match else url.split('/')[-1]
            elif platform == 'flipkart':
                # Flipkart product ID extraction
                match = re.search(r'pid=([^&]+)', url)
                if match:
                    return match.group(1)
                return url.split('/')[-1].split('?')[0]
            # Add more platform-specific ID extraction logic
            return url.split('/')[-1].split('?')[0]
        except:
            return url
    
    async def _scrape_amazon(self, url: str) -> Dict:
        """Scrape Amazon product"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract product name
                name_selectors = [
                    '#productTitle',
                    '.product-title',
                    'h1.a-size-large'
                ]
                name = None
                for selector in name_selectors:
                    element = soup.select_one(selector)
                    if element:
                        name = element.get_text().strip()
                        break
                
                # Extract price
                price_selectors = [
                    '.a-price-whole',
                    '.a-price .a-offscreen',
                    '#priceblock_dealprice',
                    '#priceblock_ourprice',
                    '.a-price-range'
                ]
                price = 0.0
                for selector in price_selectors:
                    element = soup.select_one(selector)
                    if element:
                        price = self.extract_price(element.get_text())
                        if price > 0:
                            break
                
                # Extract image
                image_selectors = [
                    '#landingImage',
                    '.a-dynamic-image',
                    'img[data-old-hires]'
                ]
                image_url = None
                for selector in image_selectors:
                    element = soup.select_one(selector)
                    if element:
                        image_url = element.get('src') or element.get('data-old-hires')
                        break
                
                # Check stock status
                stock_status = "in_stock"
                out_of_stock_indicators = [
                    "Currently unavailable",
                    "Out of stock",
                    "Temporarily out of stock"
                ]
                page_text = soup.get_text().lower()
                for indicator in out_of_stock_indicators:
                    if indicator.lower() in page_text:
                        stock_status = "out_of_stock"
                        break
                
                return {
                    "name": name or "Amazon Product",
                    "price": price,
                    "original_price": price,
                    "currency": "INR",
                    "image_url": image_url,
                    "stock_status": stock_status,
                    "product_id": self.extract_product_id(url, 'amazon'),
                    "discount": 0
                }
                
        except Exception as e:
            logger.error(f"Amazon scraping error: {e}")
            return {"error": str(e)}
    
    async def _scrape_flipkart(self, url: str) -> Dict:
        """Scrape Flipkart product"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract product name
                name_selectors = [
                    '.B_NuCI',
                    '.x2Hjhg',
                    '._35KyD6',
                    'h1 span'
                ]
                name = None
                for selector in name_selectors:
                    element = soup.select_one(selector)
                    if element:
                        name = element.get_text().strip()
                        break
                
                # Extract price
                price_selectors = [
                    '._30jeq3._16Jk6d',
                    '._30jeq3',
                    '._1_WHN1',
                    '.CEmiEU'
                ]
                price = 0.0
                for selector in price_selectors:
                    element = soup.select_one(selector)
                    if element:
                        price = self.extract_price(element.get_text())
                        if price > 0:
                            break
                
                # Extract image
                image_selectors = [
                    '._396cs4._2amPTt._3qGmMb img',
                    '._2r_T1I img',
                    '.CXW8mj img'
                ]
                image_url = None
                for selector in image_selectors:
                    element = soup.select_one(selector)
                    if element:
                        image_url = element.get('src')
                        break
                
                return {
                    "name": name or "Flipkart Product",
                    "price": price,
                    "original_price": price,
                    "currency": "INR",
                    "image_url": image_url,
                    "stock_status": "in_stock",
                    "product_id": self.extract_product_id(url, 'flipkart'),
                    "discount": 0
                }
                
        except Exception as e:
            logger.error(f"Flipkart scraping error: {e}")
            return {"error": str(e)}
    
    async def _scrape_myntra(self, url: str) -> Dict:
        """Scrape Myntra product"""
        # Basic implementation - can be enhanced
        return await self._generic_scrape(url, 'myntra')
    
    async def _scrape_meesho(self, url: str) -> Dict:
        """Scrape Meesho product"""
        return await self._generic_scrape(url, 'meesho')
    
    async def _scrape_snapdeal(self, url: str) -> Dict:
        """Scrape Snapdeal product"""
        return await self._generic_scrape(url, 'snapdeal')
    
    async def _scrape_ebay(self, url: str) -> Dict:
        """Scrape eBay product"""
        return await self._generic_scrape(url, 'ebay')
    
    async def _generic_scrape(self, url: str, platform: str) -> Dict:
        """Generic scraper for other platforms"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Generic selectors - may need adjustment per platform
                title = soup.find('title')
                name = title.get_text().strip() if title else f"{platform.title()} Product"
                
                # Try to find price with common patterns
                price_patterns = [r'₹[\d,]+', r'Rs[\d,]+', r'INR[\d,]+']
                price = 0.0
                page_text = soup.get_text()
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        price = self.extract_price(matches[0])
                        break
                
                return {
                    "name": name[:100],  # Limit name length
                    "price": price,
                    "original_price": price,
                    "currency": "INR",
                    "image_url": None,
                    "stock_status": "in_stock",
                    "product_id": self.extract_product_id(url, platform),
                    "discount": 0
                }
                
        except Exception as e:
            logger.error(f"{platform} scraping error: {e}")
            return {"error": str(e)}

scraper_manager = ScraperManager()
