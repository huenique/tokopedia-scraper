"""
CSV Writer for Tokopedia Scraper
=================================

Writes scraped product data to CSV format matching the unified template.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List


class TokopediaCSVWriter:
    """Writes Tokopedia scraped data to CSV format."""

    # CSV headers matching the template
    HEADERS = [
        "Listing Title*",
        "Listings URL*",
        "Image URL*",
        "Marketplace*",
        "Price*",
        "Shipping",
        "Units Available",
        "Item Number",
        "Brand",
        "ASIN",
        "UPC",
        "Walmart ID",
        "Seller's Name*",
        "Seller's URL*",
        "Seller's Business Name",
        "Seller's Address",
        "Seller's Email",
        "Seller's Phone Number",
    ]

    def __init__(self, output_path: str | Path):
        """
        Initialize the CSV writer.

        Args:
            output_path: Path to the output CSV file
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_products(self, products: List[Dict[str, Any]]) -> int:
        """
        Write products to CSV file.

        Args:
            products: List of product dictionaries from the scraper

        Returns:
            Number of products written
        """
        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            writer.writeheader()

            for product in products:
                row = self._format_product(product)
                writer.writerow(row)

        return len(products)

    def _format_product(self, product: Dict[str, Any]) -> Dict[str, str]:
        """
        Format a product dictionary to match CSV schema.

        Args:
            product: Raw product data from scraper

        Returns:
            Formatted row dictionary
        """
        # Extract and format price (remove currency symbols)
        price = self._extract_price(product.get("Sale Price", ""))

        return {
            "Listing Title*": product.get("Title", ""),
            "Listings URL*": product.get("Product URL", ""),
            "Image URL*": product.get("Image URL", ""),
            "Marketplace*": "Tokopedia",
            "Price*": price,
            "Shipping": "",  # Not available in current data
            "Units Available": "",  # Not available in current data
            "Item Number": product.get("Product ID", ""),
            "Brand": product.get("Brand", ""),
            "ASIN": "",  # Not applicable for Tokopedia
            "UPC": "",  # Not available
            "Walmart ID": "",  # Not applicable
            "Seller's Name*": product.get("Store Name", ""),
            "Seller's URL*": product.get("Store URL", ""),
            "Seller's Business Name": "",  # Not available in current data
            "Seller's Address": product.get("Location", ""),
            "Seller's Email": "",  # Not available
            "Seller's Phone Number": "",  # Not available
        }

    def _extract_price(self, price_str: str) -> str:
        """
        Extract numeric price from price string.

        Args:
            price_str: Price string like "Rp1.246.072"

        Returns:
            Numeric price string like "1246072"
        """
        if not price_str:
            return ""

        # Remove currency symbols and spaces
        # Convert Indonesian format (Rp1.246.072) to number (1246072)
        price_clean = re.sub(r"[^\d,.]", "", price_str)

        # Handle Indonesian number format (dots as thousands separator)
        if "." in price_clean and "," not in price_clean:
            # Likely Indonesian format: 1.246.072
            price_clean = price_clean.replace(".", "")
        elif "," in price_clean:
            # Could be: 1,246.07 or 1.246,07
            # If last separator is comma, it's European format
            if price_clean.rfind(",") > price_clean.rfind("."):
                price_clean = price_clean.replace(".", "").replace(",", ".")
            else:
                price_clean = price_clean.replace(",", "")

        try:
            return str(float(price_clean))
        except ValueError:
            return price_clean
