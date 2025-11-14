import logging
import re
from typing import List, Optional
from bs4 import BeautifulSoup

from base import BaseScraper, Product, DatabaseManager

logger = logging.getLogger(__name__)


class MarksAndSpencerHKScraper(BaseScraper):
    """Scraper for Marks & Spencer Hong Kong website"""

    def __init__(self):
        super().__init__('https://www.marksandspencer.hk', use_selenium=True)
        self.food_categories = [
            '/en/food/category/frozen-food',
            '/en/food/category/drinks',
            '/en/food/category/food-cupboard/grains-pasta'
        ]

    def get_product_urls(self) -> List[str]:
        """Get all product URLs from M&S HK food section"""
        product_urls = set()

        # Scrape each food category
        for category in self.food_categories:
            logger.info(f"Scraping category: {category}")
            category_url = f"{self.base_url}{category}"

            soup = self.fetch_page(category_url)
            if not soup:
                continue

            # Scroll to load all products
            self.scroll_page()

            # Re-parse after scrolling
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find product links - adjust selectors based on actual HTML
            # Common patterns for M&S product links
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                # M&S product URLs typically contain '/products/' or '/food/products/'
                if '/products/' in href and '/food/' in href:
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    product_urls.add(full_url)

            logger.info(f"Found {len(product_urls)} unique products so far")

        return list(product_urls)

    def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape a single product from M&S HK"""
        soup = self.fetch_page(url)
        if not soup:
            return None

        try:
            # Extract product name
            name = None
            name_selectors = [
                'h1[class*="product"]',
                'h1[class*="title"]',
                '.pdp-title',
                'h1.heading-1',
                '[data-testid="product-title"]'
            ]
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    name = elem.get_text(strip=True)
                    break

            # Extract pack size
            pack_size_quantity = None
            pack_size_unit = None
            pack_size_selectors = [
                '.ProductTitlePrice_productInfo__PtbHb .ProductTitlePrice_packSize__SAa89',
                '.ProductTitlePrice_productInfo__PtbHb span.my-1',
                'span.ProductTitlePrice_packSize__SAa89',
                '.pack-size',
                '[class*="packSize"]'
            ]
            for selector in pack_size_selectors:
                elem = soup.select_one(selector)
                if elem:
                    pack_size_text = elem.get_text(strip=True).replace('Pack size - ', '').replace('Pack size -', '')
                    # Parse quantity and unit (e.g., "165 g" -> 165, "g")
                    match = re.match(r'([\d.]+)\s*([a-zA-Z]+)', pack_size_text)
                    if match:
                        pack_size_quantity = float(match.group(1))
                        pack_size_unit = match.group(2)
                    break

            # Extract price
            price = 0.0
            price_selectors = [
                '.ProductTitlePrice_productInfo__PtbHb .heading-lg-bold',
                '.ProductTitlePrice_productInfo__PtbHb p.heading-lg-bold',
                'div.ProductTitlePrice_productInfo__PtbHb p',
                '[class*="price"][class*="current"]',
                '[class*="price"][class*="sale"]',
                '.price-value',
                '[data-testid="product-price"]',
                'span[class*="price"]'
            ]
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price = self._extract_price(elem.get_text(strip=True))
                    if price > 0:
                        break

            # Extract original price (for discounts)
            original_price = None
            original_price_selectors = [
                '[class*="original"]',
                '[class*="was"]',
                '[class*="strike"]',
                '.price-was'
            ]
            for selector in original_price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    original_price = self._extract_price(elem.get_text(strip=True))
                    if original_price and original_price > price:
                        break

            # Calculate discount
            discount = None
            if original_price and price and original_price > price:
                discount = round(((original_price - price) / original_price) * 100, 2)

            # Extract SKU
            sku = None
            sku_patterns = [
                r'sku["\']?\s*:\s*["\']?(\w+)',
                r'product[_-]?id["\']?\s*:\s*["\']?(\w+)',
                r'/products?/[^/]+/(\w+)'
            ]
            page_text = str(soup)
            for pattern in sku_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    sku = match.group(1)
                    break

            # Extract from URL if not found
            if not sku:
                match = re.search(r'/(\d+)/?$', url)
                if match:
                    sku = match.group(1)

            # Extract category from breadcrumbs
            category = None
            breadcrumb = soup.select('.breadcrumb a, [class*="breadcrumb"] a')
            if breadcrumb:
                categories = [b.get_text(strip=True) for b in breadcrumb if b.get_text(strip=True)]
                category = ' > '.join(categories) if categories else None

            # Extract description
            description = None
            desc_selectors = [
                '[class*="description"]',
                '[class*="details"]',
                '.product-info',
                '[data-testid="product-description"]'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get_text(strip=True)[:500]  # Limit length
                    break

            # Extract image
            image_url = None
            img_selectors = [
                'img[class*="product"]',
                'img[class*="main"]',
                '.product-image img',
                '[data-testid="product-image"]'
            ]
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img and img.get('src'):
                    src = img['src']
                    image_url = src if src.startswith('http') else f"{self.base_url}{src}"
                    break

            # Check stock status
            in_stock = True
            out_of_stock_indicators = [
                'out of stock',
                'sold out',
                'unavailable',
                'not available'
            ]
            page_text_lower = soup.get_text().lower()
            for indicator in out_of_stock_indicators:
                if indicator in page_text_lower:
                    in_stock = False
                    break

            if not name:
                logger.warning(f"Could not extract product name from {url}")
                return None

            return Product(
                name=name,
                price=price,
                currency='HKD',
                url=url,
                sku=sku,
                original_price=original_price,
                discount_percentage=discount,
                category=category,
                brand='Marks & Spencer',
                image_url=image_url,
                description=description,
                pack_size_quantity=pack_size_quantity,  # Changed
                pack_size_unit=pack_size_unit,  # Changed
                in_stock=in_stock
            )

        except Exception as e:
            logger.error(f"Error parsing product {url}: {e}")
            return None

    def _extract_price(self, text: str) -> float:
        """Extract numeric price from text"""
        if not text:
            return 0.0
        # Remove currency symbols and extract number
        text = text.replace(',', '').replace('$', '').replace('HKD', '').strip()
        match = re.search(r'[\d]+\.?\d*', text)
        return float(match.group()) if match else 0.0

def main():
    """Main execution function"""
    db_path = 'products.db'
    db = DatabaseManager(db_path)
    scraper = None

    try:
        # Initialize database
        db.connect()
        db.create_tables()

        # Initialize scraper
        scraper = MarksAndSpencerHKScraper()

        # Scrape products and save each one immediately
        products = scraper.scrape_all(db_manager=db)

        # Print statistics
        if products:
            stats = db.get_stats()
            logger.info("=" * 50)
            logger.info("SCRAPING COMPLETE - Statistics:")
            logger.info(f"Total Products: {stats.get('total_products', 0)}")
            logger.info(f"Discounted Products: {stats.get('discounted_products', 0)}")
            logger.info(f"Average Price: HKD {stats.get('average_price', 0)}")
            logger.info("\nTop Categories:")
            for cat, count in stats.get('top_categories', []):
                logger.info(f"  {cat}: {count} products")
            logger.info("=" * 50)
        else:
            logger.warning("No products were scraped")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

    finally:
        if scraper:
            scraper.close()
        db.close()


if __name__ == "__main__":
    main()