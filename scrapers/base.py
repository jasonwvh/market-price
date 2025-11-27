"""
===============================================================================
COMPLETE E-COMMERCE SCRAPER PACKAGE
===============================================================================

This file contains all three modules. Save this file and run the setup script
at the bottom to generate the individual files.

USAGE:
1. Save this entire file as 'setup_scrapers.py'
2. Run: python setup_scrapers.py
3. It will create:
   - base_scraper.py
   - pns_scraper.py
   - marks_spencer_scraper.py

===============================================================================
"""
import logging
import re
import firebase_admin
from firebase_admin import credentials, firestore
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Product(BaseModel):
    """Product data model"""
    name: str
    price: float
    currency: str
    url: str
    sku: Optional[str] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    pack_size_quantity: Optional[float] = None
    pack_size_unit: Optional[str] = None
    in_stock: bool = True
    scraped_at: datetime = datetime.now()


class BaseScraper(ABC):
    """Abstract base class for website scrapers"""

    def __init__(self, base_url: str, use_selenium: bool = False):
        self.base_url = base_url
        self.use_selenium = use_selenium
        self.driver = None

        if use_selenium:
            self._setup_selenium()

    def _setup_selenium(self):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Selenium WebDriver initialized")

    def fetch_page(self, url: str, delay: float = 2.0, wait_for_selector: str = "body") -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage"""
        try:
            time.sleep(delay)
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, wait_for_selector))
            )

            # Additional wait for dynamic content
            time.sleep(3)

            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def scroll_page(self, scroll_pause: float = 2.0):
        """Scroll page to load lazy-loaded content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height

    def extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text from first matching selector"""
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None

    def extract_price(self, text: str) -> float:
        """Extract numeric price from text"""
        if not text:
            return 0.0
        # Remove currency symbols and extract number
        text = text.replace(',', '').replace('$', '').replace('HKD', '').replace('HK', '').strip()
        match = re.search(r'[\\d]+\\.?\\d*', text)
        return float(match.group()) if match else 0.0

    def parse_pack_size(self, text: str) -> tuple[Optional[float], Optional[str]]:
        """Parse pack size into quantity and unit"""
        if not text:
            return None, None

        # Clean up text
        text = text.replace('Pack size - ', '').replace('Pack size -', '').strip()

        # Parse quantity and unit (e.g., "165 g" -> 165, "g")
        match = re.match(r'([\\d.]+)\\s*([a-zA-Z]+)', text)
        if match:
            quantity = float(match.group(1))
            unit = match.group(2)
            return quantity, unit

        return None, None

    def extract_image(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract image URL from first matching selector"""
        for selector in selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                src = img['src']
                return src if src.startswith('http') else f"{self.base_url}{src}"
        return None

    def check_stock(self, soup: BeautifulSoup, out_of_stock_indicators: List[str] = None) -> bool:
        """Check if product is in stock"""
        if out_of_stock_indicators is None:
            out_of_stock_indicators = [
                'out of stock',
                'sold out',
                'unavailable',
                'not available'
            ]

        page_text_lower = soup.get_text().lower()
        for indicator in out_of_stock_indicators:
            if indicator in page_text_lower:
                return False
        return True

    @abstractmethod
    def get_product_urls(self) -> List[str]:
        """Get all product URLs from the website"""
        pass

    @abstractmethod
    def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape a single product page"""
        pass

    def scrape_all(self, db_manager=None) -> List[Product]:
        """Scrape all products"""
        logger.info(f"Starting scrape of {self.base_url}")
        product_urls = self.get_product_urls()
        logger.info(f"Found {len(product_urls)} products")

        products = []
        for i, url in enumerate(product_urls, 1):
            logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
            product = self.scrape_product(url)
            if product:
                products.append(product)
                # Upsert immediately if db_manager is provided
                if db_manager:
                    db_manager.upsert_products([product])
                    logger.info(f"Product saved to database: {product.name}")

        logger.info(f"Successfully scraped {len(products)} products")
        return products

    def close(self):
        """Close the scraper and cleanup"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


class FirebaseManager:
    """Handles Firestore database operations"""

    def __init__(self, cred_path: str = '../firebase_credentials.json'):
        self.db = None
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                logger.info("Firebase connection established.")
            except Exception as e:
                logger.error(f"Firebase connection failed: {e}")
                raise
        else:
            self.db = firestore.client()

    def upsert_products(self, products: List[Product]):
        """Insert or update products in Firestore"""
        if not products:
            logger.warning("No products to insert")
            return

        batch = self.db.batch()
        products_ref = self.db.collection('products')

        for p in products:
            # Use product URL as the document ID
            doc_id = p.url.replace('/', '_').replace(':', '_')
            doc_ref = products_ref.document(doc_id)
            product_data = p.dict()
            product_data['scraped_at'] = p.scraped_at.isoformat()
            batch.set(doc_ref, product_data, merge=True)

        try:
            batch.commit()
            logger.info(f"Successfully inserted/updated {len(products)} products in Firestore")
        except Exception as e:
            logger.error(f"Error inserting products into Firestore: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics from Firestore"""
        try:
            products_ref = self.db.collection('products')
            total = products_ref.stream()
            total_products = len(list(total))

            discounted = products_ref.where('discount_percentage', '>', 0).stream()
            discounted_products = len(list(discounted))

            # Firestore doesn't support AVG aggregation directly, so we calculate it manually
            prices = [doc.to_dict().get('price', 0) for doc in products_ref.stream()]
            avg_price = sum(prices) / len(prices) if prices else 0

            # Top brands and categories (requires more complex queries or data duplication)
            # For simplicity, we'll skip this for now.
            top_brands = []
            top_categories = []

            return {
                'total_products': total_products,
                'discounted_products': discounted_products,
                'average_price': round(avg_price, 2),
                'top_brands': top_brands,
                'top_categories': top_categories
            }
        except Exception as e:
            logger.error(f"Error getting stats from Firestore: {e}")
            return {}

    def close(self):
        """No explicit close needed for Firestore client"""
        logger.info("Firebase connection managed automatically.")
