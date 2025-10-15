#!/usr/bin/env python3
"""
Unified CSV Formatter for Tokopedia Scraper

This module formats Tokopedia product and seller data to match the new
unified CSV format for uploading listings.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, cast

# Add parent directory to path to import unified modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_csv_writer import UnifiedCSVWriter


class TokopediaUnifiedFormatter:
    """Formats Tokopedia scraped data into unified CSV format."""

    def __init__(self, marketplace: str = "tokopedia"):
        self.marketplace = marketplace

    def format_product_to_unified(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Tokopedia product data to unified listing format.

        Args:
            product_data: Raw product data from Tokopedia scraper

        Returns:
            Dictionary with unified field names
        """
        # Extract image URL (handle both single string and list)
        image_url = ""
        if "product_image_urls" in product_data:
            images = product_data["product_image_urls"]
            if isinstance(images, list) and len(cast(List[Any], images)) > 0:
                image_url = str(cast(Any, images[0]))
            elif isinstance(images, str):
                image_url = images
        elif "image_url" in product_data:
            image_url = str(product_data["image_url"])

        # Extract price
        price_str = str(product_data.get("price", "0"))
        # Remove currency symbols (IDR, Rp) and extract numeric value
        import re
        price_match = re.search(r"[\d,.]+", price_str)
        price = price_match.group(0) if price_match else "0"

        # Extract seller information
        seller_name = product_data.get("seller_name", product_data.get("store_name", "Unknown Seller"))
        seller_url = product_data.get("seller_profile_url", product_data.get("store_url", ""))

        # Build unified format (using original field names - UnifiedCSVWriter will convert)
        unified_data: Dict[str, Any] = {
            "product_title": product_data.get("product_title", product_data.get("title", "")),
            "listing_url": product_data.get("listing_url", product_data.get("url", product_data.get("product_url", ""))),
            "image_url": image_url,
            "price": price,
            "item_number": product_data.get("item_number", product_data.get("product_id", product_data.get("sku", ""))),
            "seller_name": seller_name,
            "seller_url": seller_url,
            # Optional fields
            "currency": product_data.get("currency", "IDR"),
            "shipping": product_data.get("shipping", product_data.get("shipping_cost", "")),
            "units_available": product_data.get("units_available", product_data.get("stock", "")),
            "seller_business_name": product_data.get("seller_business_name", ""),
            "seller_address": product_data.get("physical_address", ""),
            "seller_email": product_data.get("email_address", ""),
            "seller_phone": product_data.get("phone_number", ""),
        }

        return unified_data

    def process_products(
        self, products: List[Dict[str, Any]], output_file: str | Path
    ) -> int:
        """
        Process multiple products and write to unified CSV format.

        Args:
            products: List of product dictionaries
            output_file: Path to output CSV file

        Returns:
            Number of products processed
        """
        output_path = Path(output_file)
        processed_count = 0

        with UnifiedCSVWriter(marketplace=self.marketplace, output_dir=str(output_path.parent)) as writer:
            for product in products:
                try:
                    unified_data = self.format_product_to_unified(product)
                    writer.add_listing(unified_data)
                    processed_count += 1
                except Exception as e:
                    print(f"⚠️  Error processing product: {e}")
                    continue

        print(f"✅ Processed {processed_count}/{len(products)} products")
        print(f"📄 Output saved to: {output_path}")

        return processed_count


def main():
    """Test the formatter with sample data."""
    # Sample Tokopedia product data
    sample_products: List[Dict[str, Any]] = [
        {
            "product_title": "Tokopedia Product 1",
            "listing_url": "https://tokopedia.com/product/1234567890",
            "product_image_urls": ["https://images.tokopedia.net/image1.jpg"],
            "price": "Rp 299.000",
            "item_number": "TK1234567890",
            "seller_name": "Tokopedia Store 1",
            "seller_profile_url": "https://tokopedia.com/store1",
            "currency": "IDR",
            "shipping": "Gratis Ongkir",
            "units_available": "100",
        },
        {
            "product_title": "Tokopedia Product 2",
            "listing_url": "https://tokopedia.com/product/9876543210",
            "product_image_urls": ["https://images.tokopedia.net/image2.jpg"],
            "price": "Rp 450.000",
            "item_number": "TK9876543210",
            "seller_name": "Tokopedia Store 2",
            "seller_profile_url": "https://tokopedia.com/store2",
            "currency": "IDR",
            "units_available": "50",
        },
    ]

    formatter = TokopediaUnifiedFormatter()
    formatter.process_products(
        sample_products, "test_results/tokopedia_unified_listings.csv"
    )


if __name__ == "__main__":
    main()
