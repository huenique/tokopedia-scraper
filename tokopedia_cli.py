#!/usr/bin/env python3
"""
Tokopedia CLI Scraper - Simplified Version

A command-line tool to scrape product information from Tokopedia.com with
infinite scrolling when no --max-pages is specified.

Usage:
    python tokopedia_cli.py -k "smartphone" -b "iPhone"
    python tokopedia_cli.py -k "smartphone" -b "iPhone" --max-pages 3
    python tokopedia_cli.py -k "laptop" -b "MacBook" --delay 3.0
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any
from urllib.parse import quote, urljoin

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from playwright.async_api import Locator, Page


class TokopediaTranslator:
    """Handles Indonesian to English translation for e-commerce terms."""

    def __init__(self) -> None:
        self.translation_map: dict[str, str] = {
            # Product terms
            "Handphone": "Smartphone",
            "Smartphone": "Smartphone",
            "Tablet": "Tablet",
            "Bekas": "Used",
            "Baru": "New",
            "Second": "Second Hand",
            "Mulus": "Excellent Condition",
            "Original": "Original",
            "Ori": "Original",
            "Garansi": "Warranty",
            "Resmi": "Official",
            "Fullset": "Complete Set",
            "BNIB": "Brand New In Box",
            "Segel": "Sealed",
            "SEIN": "Official Distributor",
            # Store and shipping terms
            "Gratis": "Free",
            "Ongkir": "Shipping",
            "Gratis Ongkir": "Free Shipping",
            "Beli Sekarang": "Buy Now",
            "Masuk Keranjang": "Add to Cart",
            "Tambah ke Wishlist": "Add to Wishlist",
            # Product info terms
            "Stok": "Stock",
            "Terjual": "Sold",
            "Rating": "Rating",
            "Ulasan": "Reviews",
            "Diskusi": "Discussion",
            "Deskripsi": "Description",
            "Spesifikasi": "Specifications",
            # Location terms
            "Jakarta": "Jakarta",
            "Surabaya": "Surabaya",
            "Bandung": "Bandung",
            "Medan": "Medan",
            "Kab.": "Regency",
            "Kota": "City",
        }

    def translate(self, text: str) -> str:
        """Translate Indonesian text to English."""
        if not text:
            return text

        # Split text into words while preserving spaces and punctuation
        words: list[str] = re.findall(r"\b\w+\b|\s+|[^\w\s]", text)
        translated_parts: list[str] = []

        for part in words:
            if part.strip() in self.translation_map:
                translated_parts.append(self.translation_map[part.strip()])
            else:
                translated_parts.append(part)

        return "".join(translated_parts)


class TokopediaScraper:
    """Main scraper class with CLI configuration support."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.translator = TokopediaTranslator()
        self.scraped_products: list[dict[str, Any]] = []

    def extract_product_id_from_url(self, url: str) -> str:
        """Extract product ID from Tokopedia URL."""
        if not url:
            return ""

        # Common Tokopedia URL patterns
        patterns = [
            r"extParam[^&]*search_id%3D([A-Z0-9]+)",  # From extParam
            r"-(\d{13,})",  # Long numeric ID (13+ digits)
            r"/([^/?]+)\?",  # Product slug before query params
            r"/([^/?]+)$",  # Product slug at end
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return url.split("/")[-1].split("?")[0] if url else ""

    def clean_price(self, price_text: str) -> str:
        """Clean and format price text."""
        if not price_text:
            return ""

        # Remove everything except digits, dots, and commas
        cleaned = re.sub(r"[^\d.,]", "", price_text)
        if cleaned:
            return f"Rp{cleaned}"
        return price_text

    def extract_store_id_from_url(self, url: str) -> str:
        """Extract store ID/slug from Tokopedia URL."""
        if not url:
            return ""

        # Extract store name from URL pattern: tokopedia.com/storename/product
        match = re.search(r"tokopedia\.com/([^/?]+)", url)
        if match:
            store_slug = match.group(1)
            # Skip common non-store pages
            if store_slug not in [
                "p",
                "discovery",
                "help",
                "about",
                "careers",
                "search",
            ]:
                return store_slug

        return ""

    def build_search_url(self) -> str:
        """Build search URL based on keyword and brand configuration."""
        keyword: str = self.config["keyword"].lower()
        brand: str = self.config.get("brand", "").lower()

        # Map keywords to category pages that work better
        category_mapping: dict[str, str] = {
            "smartphone": "handphone-tablet/handphone",
            "phone": "handphone-tablet/handphone",
            "handphone": "handphone-tablet/handphone",
            "iphone": "handphone-tablet/handphone",
            "android": "handphone-tablet/handphone",
            "samsung": "handphone-tablet/handphone",
            "xiaomi": "handphone-tablet/handphone",
            "oppo": "handphone-tablet/handphone",
            "vivo": "handphone-tablet/handphone",
            "huawei": "handphone-tablet/handphone",
            "tablet": "handphone-tablet/tablet",
            "ipad": "handphone-tablet/tablet",
            "laptop": "komputer-laptop/laptop",
            "komputer": "komputer-laptop",
            "macbook": "komputer-laptop/laptop",
            "headphone": "elektronik/audio",
            "earphone": "elektronik/audio",
            "speaker": "elektronik/audio",
            "audio": "elektronik/audio",
            "lego": "mainan-hobi",
            "toy": "mainan-hobi",
            "mainan": "mainan-hobi",
            "game": "mainan-hobi/games",
            "konsol": "elektronik/gaming",
            "playstation": "elektronik/gaming",
            "xbox": "elektronik/gaming",
            "nintendo": "elektronik/gaming",
            "fashion": "fashion",
            "baju": "fashion-pria",
            "kaos": "fashion-pria",
            "jaket": "fashion-pria",
            "sepatu": "sepatu-pria",
            "tas": "tas-travel",
            "jam": "jam-tangan",
            "watch": "jam-tangan",
            "kamera": "kamera-foto-video",
            "camera": "kamera-foto-video",
            "tv": "elektronik/televisi-video",
            "television": "elektronik/televisi-video",
        }

        # Try to find a category match
        category: str | None = None
        for key, cat in category_mapping.items():
            if key in keyword:
                category = cat
                break

        if category:
            # Use category page (more reliable)
            return f"https://www.tokopedia.com/p/{category}"
        else:
            # Fallback to search page
            search_query: str = f"{brand} {keyword}".strip() if brand else keyword
            encoded_query: str = quote(search_query)
            return f"https://www.tokopedia.com/search?st=product&q={encoded_query}"

    async def handle_page_with_scroll(self, context: PlaywrightCrawlingContext) -> None:
        """Handle page with infinite scrolling or limited scrolling."""
        page: Page = context.page
        request = context.request

        print(f"🔍 Processing: {request.url}")

        # Wait for page to load completely
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(self.config.get("delay", 2))

        max_pages: int | None = self.config.get("max_pages")
        scraped_count: int = 0
        scroll_attempts: int = 0

        # Set scroll limit based on max_pages
        if max_pages:
            max_scroll_attempts: int = max_pages * 5  # Assume 5 scrolls per "page"
            print(
                f"   🎯 Target: ~{max_pages} pages ({max_scroll_attempts} scroll attempts)"
            )
        else:
            max_scroll_attempts: int = 200  # Reasonable limit for infinite scroll
            print(f"   ♾️ Mode: Infinite scroll (up to {max_scroll_attempts} attempts)")

        while scroll_attempts < max_scroll_attempts:
            # Look for product containers
            product_containers: list[Locator] = await page.locator(
                'div[data-testid="divProductWrapper"]'
            ).all()

            if len(product_containers) == 0:
                # Try alternative selectors for different page types
                product_containers = await page.locator(
                    'a[data-testid="lnkProductContainer"]'
                ).all()

            # If still no containers, try search page selectors
            if len(product_containers) == 0:
                product_containers = await page.locator(
                    '[data-testid*="product"], [data-testid*="Product"]'
                ).all()

            # If still none, try CSS class based selectors
            if len(product_containers) == 0:
                product_containers = await page.locator(
                    '.prd_container-card, .css-bk6tzz, .css-5wh65g, [class*="product"]'
                ).all()

            print(f"   🔍 Found {len(product_containers)} product containers")

            # Extract data from new products (skip already processed ones)
            new_products: int = 0
            for i, container in enumerate(
                product_containers[scraped_count:], start=scraped_count
            ):
                try:
                    product_data: dict[
                        str, Any
                    ] = await self.extract_product_from_container(container, page.url)
                    if product_data and product_data.get("Title"):
                        self.scraped_products.append(product_data)
                        new_products += 1
                        print(
                            f"   ✓ {len(self.scraped_products)}: {product_data.get('Title', 'Unknown')[:50]}..."
                        )

                except Exception as e:
                    print(f"   ✗ Error extracting product {i + 1}: {e}")
                    continue

            scraped_count = len(product_containers)

            # If we have max_pages set and reached our target, stop
            if max_pages and scroll_attempts >= max_pages * 5:
                print(f"   📊 Reached target scroll attempts for {max_pages} pages")
                break

            # Scroll down to load more products
            print(
                f"   🔄 Scrolling... (attempt {scroll_attempts + 1}/{max_scroll_attempts})"
            )

            # Get current product count before scrolling
            products_before_scroll: int = len(product_containers)

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self.config.get("delay", 2))

            # Check if new products loaded
            await page.wait_for_load_state("networkidle", timeout=10000)
            new_containers: list[Locator] = await page.locator(
                'div[data-testid="divProductWrapper"]'
            ).all()

            if len(new_containers) == 0:
                new_containers = await page.locator(
                    'a[data-testid="lnkProductContainer"]'
                ).all()

            # If no new products loaded, we've reached the end
            if len(new_containers) <= products_before_scroll:
                print(f"   📋 No more products to load. Reached end of page.")
                break

            scroll_attempts += 1

        print(f"   📊 Total products scraped: {len(self.scraped_products)}")
        print(f"   📜 Scroll attempts completed: {scroll_attempts}")

    async def extract_product_from_container(
        self, container: Locator, base_url: str
    ) -> dict[str, Any]:
        """Extract comprehensive product data from a container element."""
        try:
            # Extract product URL
            product_url: str = ""
            try:
                # Check if container itself is a link
                href: str | None = await container.get_attribute("href")
                if href:
                    product_url = href
                else:
                    # Look for link within container
                    link: Locator = container.locator("a").first
                    if await link.count() > 0:
                        href = await link.get_attribute("href")
                        if href:
                            product_url = href
            except Exception:
                pass

            # Make URL absolute
            if product_url and not product_url.startswith("http"):
                if product_url.startswith("/"):
                    product_url = f"https://www.tokopedia.com{product_url}"
                else:
                    product_url = urljoin(base_url, product_url)

            # Extract title using multiple possible selectors
            title: str = ""
            title_selectors: list[str] = [
                ".css-20kt3o",  # Primary title class (category pages)
                'span[data-testid*="spnSRPProdName"]',  # Search result product name
                'span[data-testid*="title"]',
                'span[data-testid*="name"]',
                'div[data-testid*="title"]',
                'span[class*="title"]',
                'span[class*="name"]',
                'span[class*="prd_link-prod-name"]',  # Search page product name
                ".css-3017qm",  # Alternative title class
                'span[data-unify="Typography"]',  # Typography component
                "h3",
                "h4",
                "h5",  # Generic headings
                "a[title]",  # Links with title attribute
                '[class*="name"]',
                '[class*="title"]',  # Generic class patterns
            ]

            for selector in title_selectors:
                try:
                    title_elem: Locator = container.locator(selector).first
                    if await title_elem.count() > 0:
                        title_text: str = await title_elem.inner_text()
                        if (
                            title_text
                            and title_text.strip()
                            and len(title_text.strip()) > 5
                        ):
                            title = title_text.strip()
                            break
                        # Also try title attribute if inner text is empty
                        title_attr: str | None = await title_elem.get_attribute("title")
                        if (
                            title_attr
                            and title_attr.strip()
                            and len(title_attr.strip()) > 5
                        ):
                            title = title_attr.strip()
                            break
                except:
                    continue

            # Extract price
            price: str = ""
            price_selectors: list[str] = [
                ".css-o5uqvq",  # Primary price class (category pages)
                'span[data-testid*="spnSRPProdPrice"]',  # Search result price
                'span[class*="price"]',
                'div[class*="price"]',
                'span:has-text("Rp")',
                'div:has-text("Rp")',
                ".css-h66vau",  # Alternative price class
                ".prd_link-prod-price",  # Search page price class
                '[class*="price"]',  # Generic price pattern
                'span[data-unify="Typography"]:has-text("Rp")',  # Typography with Rp
            ]

            for selector in price_selectors:
                try:
                    price_elem: Locator = container.locator(selector).first
                    if await price_elem.count() > 0:
                        price_text: str = await price_elem.inner_text()
                        if price_text and "Rp" in price_text:
                            price = self.clean_price(price_text)
                            break
                except:
                    continue

            # Extract store information
            store_name: str = ""
            store_location: str = ""
            store_info_selectors: list[str] = [
                ".css-ywdpwd",  # Store info class
                'span[data-testid*="spnSRPProdTablet"]',
                'span[class*="shop"]',
                'div[class*="shop"]',
                'span[class*="store"]',
                'div[class*="store"]',
            ]

            store_texts: list[str] = []
            for selector in store_info_selectors:
                try:
                    elements: list[Locator] = await container.locator(selector).all()
                    for elem in elements:
                        text: str = await elem.inner_text()
                        if text and text.strip() and len(text.strip()) > 2:
                            store_texts.append(text.strip())
                except:
                    continue

            # Parse store information
            if store_texts:
                if len(store_texts) >= 2:
                    store_location = store_texts[0]
                    store_name = store_texts[1]
                else:
                    text: str = store_texts[0]
                    if any(
                        loc in text
                        for loc in ["Jakarta", "Surabaya", "Bandung", "Kab.", "Kota"]
                    ):
                        store_location = text
                    else:
                        store_name = text

            # Extract image URL
            image_url: str = ""
            try:
                img_elem: Locator = container.locator("img").first
                if await img_elem.count() > 0:
                    image_url_raw: str | None = await img_elem.get_attribute("src")
                    if image_url_raw and not image_url_raw.startswith("http"):
                        if image_url_raw.startswith("//"):
                            image_url = f"https:{image_url_raw}"
                        else:
                            image_url = f"https://www.tokopedia.com{image_url_raw}"
                    elif image_url_raw:
                        image_url = image_url_raw
            except:
                pass

            # Skip if missing essential data
            if not title:
                return {}

            # Extract store ID and build store URL
            store_id: str = self.extract_store_id_from_url(product_url)
            store_url: str | None = (
                f"https://www.tokopedia.com/{store_id}" if store_id else None
            )

            # Build product data in the requested format
            product_data: dict[str, Any] = {
                "Product ID": self.extract_product_id_from_url(product_url),
                "Title": self.translator.translate(title),
                "Sale Price": price,
                "Original Price": price,  # Tokopedia doesn't always show original price
                "Discount (%)": 0,  # Would need specific implementation
                "Currency": "IDR",
                "Rating": None,  # Placeholder - would need specific implementation
                "Orders Count": None,  # Placeholder - would need specific implementation
                "Store Name": self.translator.translate(store_name)
                if store_name
                else None,
                "Store ID": store_id if store_id else None,
                "Store URL": store_url,
                "Product URL": product_url,
                "Image URL": image_url,
                "Brand": self.config.get("brand", ""),
                "Location": self.translator.translate(store_location)
                if store_location
                else None,
                "Scraped At": datetime.now().isoformat(),
            }

            return product_data

        except Exception as e:
            print(f"Error in extract_product_from_container: {e}")
            return {}

    async def run_scraper(self) -> list[dict[str, Any]]:
        """Run the scraper and return collected products."""
        crawler = PlaywrightCrawler(
            request_handler=self.handle_page_with_scroll,
            headless=True,
            browser_type="chromium",
            max_requests_per_crawl=1,  # Only process one page with scrolling
        )

        url: str = self.build_search_url()

        print(f"🚀 Starting Tokopedia Scraper")
        print(
            f"🔍 Search Query: {self.config.get('brand', '')} {self.config['keyword']}".strip()
        )

        max_pages: int | None = self.config.get("max_pages")
        if max_pages:
            print(f"📄 Target: ~{max_pages} pages worth of products")
        else:
            print(f"♾️ Mode: Infinite scroll (scrape ALL products)")

        print(f"🌐 URL: {url}")
        print("=" * 60)

        try:
            await crawler.run([url])
        except Exception as e:
            # If category URL fails, try search fallback
            if "status code: 410" in str(e) or "status code: 404" in str(e):
                print(f"⚠️ Category URL failed, trying search fallback...")
                search_query: str = (
                    f"{self.config.get('brand', '')} {self.config['keyword']}".strip()
                )
                encoded_query: str = quote(search_query)
                fallback_url: str = (
                    f"https://www.tokopedia.com/search?st=product&q={encoded_query}"
                )
                print(f"🌐 Fallback URL: {fallback_url}")
                await crawler.run([fallback_url])
            else:
                raise e

        print("=" * 60)
        print(f"✅ Scraping completed!")
        print(f"📊 Total products scraped: {len(self.scraped_products)}")

        return self.scraped_products


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Tokopedia Product Scraper - Simplified",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --keyword "smartphone" --brand "iPhone"
  %(prog)s -k "laptop" -b "MacBook" --max-pages 3
  %(prog)s -k "headphone" -b "Sony"
        """,
    )

    # Required arguments
    parser.add_argument("--keyword", "-k", required=True, help="Search keyword")
    parser.add_argument(
        "--brand",
        "-b",
        required=True,
        help="Brand name to associate with products (prepended to search)",
    )

    # Scraping configuration
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum pages to scrape (default: scrape all products with infinite scroll)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between scroll actions in seconds (default: 2.0)",
    )

    return parser


async def main() -> None:
    """Main CLI function."""
    parser: argparse.ArgumentParser = create_parser()
    args: argparse.Namespace = parser.parse_args()

    # Convert args to config dictionary
    config: dict[str, Any] = {
        "keyword": args.keyword,
        "brand": args.brand,
        "max_pages": args.max_pages,
        "delay": args.delay,
    }

    try:
        # Initialize and run scraper
        scraper: TokopediaScraper = TokopediaScraper(config)
        products: list[dict[str, Any]] = await scraper.run_scraper()

        # Output JSON results
        if products:
            output_json: str = json.dumps(products, indent=2, ensure_ascii=False)
            print("\n" + "=" * 60)
            print("📋 SCRAPED PRODUCTS (JSON OUTPUT):")
            print("=" * 60)
            print(output_json)

            # Also save to file
            now: datetime = datetime.now()
            date: str = now.strftime("%Y%m%d")
            unix_timestamp: int = int(time.time())
            brand: str = args.brand.lower().replace(" ", "-")
            filename: str = f"tokopedia_{brand}_{date}_{unix_timestamp}.json"
            filepath: str = f"results/{filename}"

            # Ensure results directory exists
            os.makedirs("results", exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {filepath}")
        else:
            print("\n⚠️ No products found.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
