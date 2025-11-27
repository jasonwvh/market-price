# ============================================================================
# FILE 2: pns_scraper.py
# ============================================================================


import logging
import json
from typing import List, Optional
from bs4 import BeautifulSoup

from base import BaseScraper, Product, FirebaseManager

logger = logging.getLogger(__name__)


class PNSScraper(BaseScraper):
    """Scraper for PNS (PARKnSHOP) Hong Kong website"""

    def __init__(self):
        super().__init__('https://www.pns.hk', use_selenium=True)

        # Main food & beverage categories based on PNS structure
        self.categories = [
            '/en/food-beverages/rice/c/04040100',
            # '/en/food-beverages/noodle-pasta/c/04040200',
            # '/en/food-beverages/oil/c/04040300',
            # '/en/food-beverages/baking-dessert-needs/c/04040400',
            # '/en/food-beverages/alcoholic-beverages/c/04012000',
            # '/en/food-beverages/water/c/04010100',
        ]

    def get_product_urls(self) -> List[str]:
        """Get all product URLs from PNS categories"""
        product_urls = set()

        for category in self.categories:
            logger.info(f"Scraping category: {category}")
            category_url = f"{self.base_url}{category}"

            soup = self.fetch_page(category_url)
            if not soup:
                continue

            # Scroll to load all products
            self.scroll_page(scroll_pause=2.0)

            # Re-parse after scrolling
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find product links
            # PNS uses /p/ for product pages with format: /en/product-name/p/BP_XXXXXX
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                if '/p/BP_' in href or '/p/bp_' in href:
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    product_urls.add(full_url)

            logger.info(f"Found {len(product_urls)} unique products so far")

            # Handle pagination - PNS uses ?page=X
            page_num = 1
            max_pages = 10  # Limit to prevent infinite loops

            while page_num < max_pages:
                page_num += 1
                page_url = f"{category_url}?page={page_num}"

                soup = self.fetch_page(page_url, delay=1.5)
                if not soup:
                    break

                # Check if we got new products
                old_count = len(product_urls)
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link['href']
                    if '/p/BP_' in href or '/p/bp_' in href:
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        product_urls.add(full_url)

                # If no new products found, we've reached the end
                if len(product_urls) == old_count:
                    logger.info(f"No new products on page {page_num}, moving to next category")
                    break

        return list(product_urls)

    def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape a single product from PNS"""
        soup = self.fetch_page(url)
        if not soup:
            return None

        try:
            script_tag = soup.find('script', {'id': 'ng-state'})
            if not script_tag:
                logger.warning(f"Could not find ng-state JSON in {url}")
                return None

            data = json.loads(script_tag.string)

            # The product SKU is the key within 'entities'
            # We need to find it first. We can get it from the JSON-LD script as well or find the first key.

            # --- Start: Find the dynamic SKU key ---
            # Method 1: Grab the first key found under 'entities'
            product_sku_key = None
            entities = data.get('cx-state', {}).get('product', {}).get('details', {}).get('entities', {})
            if entities:
                product_sku_key = next(iter(entities))  # Gets the first key, e.g., "22596"

            if not product_sku_key:
                logger.warning(f"Could not find product SKU key in ng-state JSON from {url}")
                return None
            # --- End: Find the dynamic SKU key ---

            # Now extract all data using this key
            product_data = entities[product_sku_key].get('details', {}).get('value', {})
            if not product_data:
                # Sometimes the data is in the 'variants' key instead
                product_data = entities[product_sku_key].get('variants', {}).get('value', {})
                if not product_data:
                    logger.warning(f"Could not find 'value' block in ng-state JSON from {url}")
                    return None

            name = product_data.get('name')
            price = product_data.get('price', {}).get('value', 0.0)
            original_price = product_data.get('price', {}).get('oldValue')  # May be None

            # Extract pack size from JSON
            pack_size_text = product_data.get('contentSizeUnit')  # This will be "330MLX12"
            pack_size_quantity, pack_size_unit = self.parse_pack_size(pack_size_text) if pack_size_text else (None,
                                                                                                              None)
            # Calculate discount
            discount = None
            if original_price and price and original_price > price:
                discount = round(((original_price - price) / original_price) * 100, 2)

            sku = product_data.get('baseProduct')  # e.g., "BP_22596"
            brand = product_data.get('supplierName')  # e.g., "DAKEN LTD"

            # Extract category
            category = None
            category_levels = product_data.get('categoryNameLevels', [])
            if category_levels:
                category = ' > '.join([c.get('name', '') for c in category_levels])

            # Extract description and clean HTML
            description_html = product_data.get('description', '')
            description = ''
            if description_html:
                description_soup = BeautifulSoup(description_html, 'html.parser')
                description = description_soup.get_text(strip=True)[:500]

            image_url = product_data.get('images', {}).get('PRIMARY', {}).get('zoom', {}).get('url')
            in_stock = product_data.get('stock', {}).get('stockLevelStatus') == 'inStock'

            if not name:
                logger.warning(f"Could not extract product name from {url}")
                return None

            return Product(
                name=name,
                price=float(price),
                currency='HKD',
                url=url,
                sku=sku,
                original_price=float(original_price) if original_price else None,
                discount_percentage=discount,
                category=category,
                brand=brand or 'PNS',  # Fallback to PNS as in your original code
                image_url=image_url,
                description=description,
                pack_size_quantity=pack_size_quantity,
                pack_size_unit=pack_size_unit,
                in_stock=in_stock
            )

        except Exception as e:
            logger.error(f"Error parsing product {url}: {e}")
            return None


def main():
    """Main execution function"""
    db = FirebaseManager()
    scraper = None

    try:
        # Initialize scraper
        scraper = PNSScraper()

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

            logger.info("\nTop Brands:")
            for brand, count in stats.get('top_brands', []):
                logger.info(f"  {brand}: {count} products")

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