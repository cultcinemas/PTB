"""
Affiliate Link Manager for Price Tracker Bot
Handles conversion of product URLs to affiliate links
"""
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class AffiliateManager:
    """
    Manages affiliate link conversion for various e-commerce platforms
    """
    
    def __init__(self):
        # Configure your affiliate tags/IDs here
        self.affiliate_config = {
            'amazon': {
                'tag': 'yourtag-21',  # Replace with your Amazon affiliate tag
                'param_name': 'tag'
            },
            'flipkart': {
                'tag': 'youraffid',  # Replace with your Flipkart affiliate ID
                'param_name': 'affid'
            },
            'myntra': {
                'tag': 'your_myntra_id',
                'param_name': 'affid'
            },
            'meesho': {
                'tag': 'your_meesho_id',
                'param_name': 'aff_id'
            },
            'snapdeal': {
                'tag': 'your_snapdeal_id',
                'param_name': 'aff_id'
            },
            'ebay': {
                'tag': 'your_ebay_campid',
                'param_name': 'campid'
            }
        }
        
        # Platform domain patterns
        self.platform_patterns = {
            'amazon': [
                r'amazon\.in',
                r'amazon\.com',
                r'amzn\.to',
                r'amzn\.in'
            ],
            'flipkart': [
                r'flipkart\.com',
                r'fkrt\.it'
            ],
            'myntra': [
                r'myntra\.com'
            ],
            'meesho': [
                r'meesho\.com'
            ],
            'snapdeal': [
                r'snapdeal\.com'
            ],
            'ebay': [
                r'ebay\.in',
                r'ebay\.com'
            ]
        }
    
    def detect_platform(self, url: str) -> Optional[str]:
        """
        Detect the e-commerce platform from URL
        
        Args:
            url: Product URL
            
        Returns:
            Platform name or None
        """
        url_lower = url.lower()
        
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform
        
        return None
    
    def convert_to_affiliate(self, url: str, platform: Optional[str] = None) -> str:
        """
        Convert a regular product URL to affiliate link
        
        Args:
            url: Original product URL
            platform: Platform name (auto-detected if None)
            
        Returns:
            Affiliate URL
        """
        try:
            # Auto-detect platform if not provided
            if platform is None:
                platform = self.detect_platform(url)
            
            if platform is None:
                logger.warning(f"Unknown platform for URL: {url}")
                return url
            
            # Get affiliate config for platform
            config = self.affiliate_config.get(platform)
            if not config:
                logger.warning(f"No affiliate config for platform: {platform}")
                return url
            
            # Platform-specific conversion
            if platform == 'amazon':
                return self._convert_amazon(url, config)
            elif platform == 'flipkart':
                return self._convert_flipkart(url, config)
            elif platform == 'myntra':
                return self._convert_myntra(url, config)
            elif platform == 'meesho':
                return self._convert_meesho(url, config)
            elif platform == 'snapdeal':
                return self._convert_snapdeal(url, config)
            elif platform == 'ebay':
                return self._convert_ebay(url, config)
            else:
                return url
                
        except Exception as e:
            logger.error(f"Error converting URL to affiliate: {e}")
            return url
    
    def _convert_amazon(self, url: str, config: Dict) -> str:
        """Convert Amazon URL to affiliate link"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Add or update affiliate tag
        query_params[config['param_name']] = [config['tag']]
        
        # Remove unwanted tracking parameters
        params_to_remove = ['qid', 'sr', 'ref', 'pd_rd_w', 'pd_rd_r', 'pd_rd_wg']
        for param in params_to_remove:
            query_params.pop(param, None)
        
        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''
        ))
        
        return new_url
    
    def _convert_flipkart(self, url: str, config: Dict) -> str:
        """Convert Flipkart URL to affiliate link"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Add affiliate ID
        query_params[config['param_name']] = [config['tag']]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''
        ))
        
        return new_url
    
    def _convert_myntra(self, url: str, config: Dict) -> str:
        """Convert Myntra URL to affiliate link"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        query_params[config['param_name']] = [config['tag']]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''
        ))
        
        return new_url
    
    def _convert_meesho(self, url: str, config: Dict) -> str:
        """Convert Meesho URL to affiliate link"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        query_params[config['param_name']] = [config['tag']]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''
        ))
        
        return new_url
    
    def _convert_snapdeal(self, url: str, config: Dict) -> str:
        """Convert Snapdeal URL to affiliate link"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        query_params[config['param_name']] = [config['tag']]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''
        ))
        
        return new_url
    
    def _convert_ebay(self, url: str, config: Dict) -> str:
        """Convert eBay URL to affiliate link"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        query_params[config['param_name']] = [config['tag']]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''
        ))
        
        return new_url
    
    def update_affiliate_config(self, platform: str, tag: str, param_name: str = None):
        """
        Update affiliate configuration for a platform
        
        Args:
            platform: Platform name
            tag: Affiliate tag/ID
            param_name: Parameter name (optional)
        """
        if platform not in self.affiliate_config:
            self.affiliate_config[platform] = {}
        
        self.affiliate_config[platform]['tag'] = tag
        
        if param_name:
            self.affiliate_config[platform]['param_name'] = param_name
        
        logger.info(f"Updated affiliate config for {platform}")

# Global instance
affiliate_manager = AffiliateManager()
