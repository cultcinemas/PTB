# test_affiliate.py
from utils.affiliate_manager import affiliate_manager

def test_platform_detection():
    urls = {
        "https://www.amazon.in/dp/B09G9BL5CP": "amazon",
        "https://www.flipkart.com/product/p/itmxyz": "flipkart",
        "https://www.myntra.com/product/123": "myntra"
    }
    
    for url, expected in urls.items():
        detected = affiliate_manager.detect_platform(url)
        assert detected == expected, f"Failed for {url}"
    
    print("✅ Platform detection tests passed")

def test_affiliate_conversion():
    test_cases = [
        {
            "url": "https://www.amazon.in/dp/B09G9BL5CP",
            "platform": "amazon",
            "should_contain": "tag="
        },
        {
            "url": "https://www.flipkart.com/product/p/itmxyz",
            "platform": "flipkart",
            "should_contain": "affid="
        }
    ]
    
    for case in test_cases:
        result = affiliate_manager.convert_to_affiliate(
            case["url"],
            case["platform"]
        )
        assert case["should_contain"] in result
        print(f"✅ {case['platform']}: {result}")
    
    print("✅ Affiliate conversion tests passed")

if __name__ == "__main__":
    test_platform_detection()
    test_affiliate_conversion()
