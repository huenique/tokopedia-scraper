#!/usr/bin/env python3
"""
Tokopedia GraphQL API Scraper

A Python module that directly calls the Tokopedia GraphQL API to scrape product information
without using browser automation. This approach is much faster and more efficient.

Usage:
    python tokopedia_graphql.py --keyword "smartphone" --brand "iPhone" --max-products 100
    python tokopedia_graphql.py -k "laptop" -b "MacBook" --pages 3
"""

import argparse
import json
import os
import random
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from urllib.parse import quote

import requests
from common.job_metadata import JobMetadata, JobStatus
from common.path_utils import PathUtils

# Import CSV writer and job metadata
from csv_writer import TokopediaCSVWriter


class TokopediaTranslator:
    """Handles Indonesian to English translation for e-commerce terms."""

    def __init__(self) -> None:
        self.translation_map: Dict[str, str] = {
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
        words: List[str] = re.findall(r"\b\w+\b|\s+|[^\w\s]", text)
        translated_parts: List[str] = []

        for part in words:
            if part.strip() in self.translation_map:
                translated_parts.append(self.translation_map[part.strip()])
            else:
                translated_parts.append(part)

        return "".join(translated_parts)


class TokopediaGraphQLScraper:
    """GraphQL API based Tokopedia scraper."""

    # GraphQL endpoint
    GRAPHQL_URL = "https://gql.tokopedia.com/graphql/SearchProductV5Query"

    # GraphQL query for product search
    GRAPHQL_QUERY = """
    query SearchProductV5Query($params: String!) {
        searchProductV5(params: $params) {
            header {
                totalData
                responseCode
                keywordProcess
                keywordIntention
                componentID
                isQuerySafe
                additionalParams
                backendFilters
                meta {
                    dynamicFields
                    __typename
                }
                __typename
            }
            data {
                totalDataText
                banner {
                    position
                    text
                    applink
                    url
                    imageURL
                    componentID
                    trackingOption
                    __typename
                }
                redirection {
                    url
                    __typename
                }
                related {
                    relatedKeyword
                    position
                    trackingOption
                    otherRelated {
                        keyword
                        url
                        applink
                        componentID
                        products {
                            oldID: id
                            id: id_str_auto_
                            name
                            url
                            applink
                            mediaURL {
                                image
                                __typename
                            }
                            shop {
                                oldID: id
                                id: id_str_auto_
                                name
                                city
                                tier
                                __typename
                            }
                            badge {
                                oldID: id
                                id: id_str_auto_
                                title
                                url
                                __typename
                            }
                            price {
                                text
                                number
                                __typename
                            }
                            freeShipping {
                                url
                                __typename
                            }
                            labelGroups {
                                position
                                title
                                type
                                url
                                styles {
                                    key
                                    value
                                    __typename
                                }
                                __typename
                            }
                            rating
                            wishlist
                            ads {
                                id
                                productClickURL
                                productViewURL
                                productWishlistURL
                                tag
                                __typename
                            }
                            meta {
                                oldWarehouseID: warehouseID
                                warehouseID: warehouseID_str_auto_
                                componentID
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                suggestion {
                    currentKeyword
                    suggestion
                    query
                    text
                    componentID
                    trackingOption
                    __typename
                }
                ticker {
                    oldID: id
                    id: id_str_auto_
                    text
                    query
                    applink
                    componentID
                    trackingOption
                    __typename
                }
                violation {
                    headerText
                    descriptionText
                    imageURL
                    ctaURL
                    ctaApplink
                    buttonText
                    buttonType
                    __typename
                }
                products {
                    oldID: id
                    id: id_str_auto_
                    ttsProductID
                    name
                    url
                    applink
                    mediaURL {
                        image
                        image300
                        videoCustom
                        __typename
                    }
                    shop {
                        oldID: id
                        id: id_str_auto_
                        ttsSellerID
                        name
                        url
                        city
                        tier
                        __typename
                    }
                    stock {
                        ttsSKUID
                        __typename
                    }
                    badge {
                        oldID: id
                        id: id_str_auto_
                        title
                        url
                        __typename
                    }
                    price {
                        text
                        number
                        range
                        original
                        discountPercentage
                        __typename
                    }
                    freeShipping {
                        url
                        __typename
                    }
                    labelGroups {
                        position
                        title
                        type
                        url
                        styles {
                            key
                            value
                            __typename
                        }
                        __typename
                    }
                    labelGroupsVariant {
                        title
                        type
                        typeVariant
                        hexColor
                        __typename
                    }
                    category {
                        oldID: id
                        id: id_str_auto_
                        name
                        breadcrumb
                        gaKey
                        __typename
                    }
                    rating
                    wishlist
                    ads {
                        id
                        productClickURL
                        productViewURL
                        productWishlistURL
                        tag
                        __typename
                    }
                    meta {
                        oldParentID: parentID
                        parentID: parentID_str_auto_
                        oldWarehouseID: warehouseID
                        warehouseID: warehouseID_str_auto_
                        isImageBlurred
                        isPortrait
                        __typename
                    }
                    __typename
                }
                __typename
            }
            __typename
        }
    }
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.translator = TokopediaTranslator()
        self.session = requests.Session()
        self.scraped_products: List[Dict[str, Any]] = []
        self.excluded_product_ids: List[str] = []
        self.search_id: Optional[str] = None

        # Setup session with realistic headers
        self._setup_session()

    def _setup_session(self) -> None:
        """Setup HTTP session with realistic headers."""
        # Generate random device IDs
        device_id = str(random.randint(1000000000000000000, 9999999999999999999))
        user_id = str(random.randint(100000000, 999999999))
        unique_id = str(uuid.uuid4()).replace("-", "")

        self.session.headers.update(
            {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "bd-device-id": device_id,
                "bd-web-id": device_id,
                "content-type": "application/json",
                "dnt": "1",
                "origin": "https://www.tokopedia.com",
                "referer": "https://www.tokopedia.com/",
                "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "tkpd-userid": user_id,
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
                "x-dark-mode": "false",
                "x-device": "desktop-0.0",
                "x-price-center": "true",
                "x-source": "tokopedia-lite",
                "x-tkpd-lite-service": "zeus",
            }
        )

        # Store IDs for use in parameters
        self.device_id = device_id
        self.user_id = user_id
        self.unique_id = unique_id

    def _build_search_params(self, query: str, page: int = 1, start: int = 0) -> str:
        """Build search parameters for GraphQL request."""
        # Base parameters
        params = {
            "device": "desktop",
            "enter_method": "normal_search",
            "l_name": "sre",
            "navsource": "home,home",
            "ob": "23",  # Sort order
            "page": str(page),
            "q": query,
            "related": "true",
            "rows": "60",  # Results per page
            "safe_search": "false",
            "sc": "",
            "scheme": "https",
            "shipping": "",
            "show_adult": "false",
            "source": "search",
            "srp_component_id": "02.01.00.00",
            "srp_page_id": "",
            "srp_page_title": "",
            "st": "product",
            "start": str(start),
            "topads_bucket": "true",
            "unique_id": self.unique_id,
            "user_addressId": "",
            "user_cityId": "176",
            "user_districtId": "2274",
            "user_id": self.user_id,
            "user_lat": "",
            "user_long": "",
            "user_postCode": "",
            "user_warehouseId": "0",
            "variants": "",
            "warehouses": "",
        }

        # Add pagination-specific parameters
        if page > 1:
            params["has_more"] = "true"
            params["next_offset_organic"] = str(start - 60)
            params["next_offset_organic_ad"] = str(start - 60)

            # Add excluded product IDs to avoid duplicates
            if self.excluded_product_ids:
                params["minus_ids"] = ",".join(self.excluded_product_ids)

            # Add search ID for consistency
            if self.search_id:
                params["search_id"] = self.search_id

        return "&".join(f"{k}={quote(str(v))}" for k, v in params.items())

    def _make_graphql_request(
        self, query: str, page: int = 1, start: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Make GraphQL request to Tokopedia API."""
        params_string = self._build_search_params(query, page, start)

        payload: List[Dict[str, Any]] = [
            {
                "operationName": "SearchProductV5Query",
                "variables": {"params": params_string},
                "query": self.GRAPHQL_QUERY,
            }
        ]

        try:
            print(f"   🔍 Making GraphQL request for page {page} (start: {start})...")

            response = self.session.post(self.GRAPHQL_URL, json=payload, timeout=30)

            if response.status_code == 200:
                data: list[Dict[str, Any]] = response.json()
                if len(data) > 0:
                    return data[0]
                return cast(Dict[str, Any], data)
            else:
                print(f"   ❌ Request failed with status {response.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ Request error: {e}")
            return None

    def _extract_search_id(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract search ID from response for pagination consistency."""
        try:
            # Search ID might be in various places in the response
            if "data" in response_data and "searchProductV5" in response_data["data"]:
                search_data = response_data["data"]["searchProductV5"]
                if "header" in search_data:
                    header = search_data["header"]
                    if "additionalParams" in header:
                        additional_params = str(header["additionalParams"])
                        # Parse additional params to find search_id
                        for param in additional_params.split("&"):
                            if param.startswith("search_id="):
                                return param.split("=", 1)[1]
            return None
        except Exception:
            return None

    def _extract_products_from_response(
        self, response_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract and format product data from GraphQL response."""
        products: List[Dict[str, Any]] = []

        try:
            if "data" in response_data and "searchProductV5" in response_data["data"]:
                search_data = response_data["data"]["searchProductV5"]

                # Extract search ID for pagination
                if not self.search_id:
                    self.search_id = self._extract_search_id(response_data)

                if "data" in search_data and "products" in search_data["data"]:
                    raw_products = search_data["data"]["products"]

                    for product in raw_products:
                        try:
                            formatted_product = self._format_product(
                                cast(Dict[str, Any], product)
                            )
                            if formatted_product:
                                products.append(formatted_product)

                                # Track product ID for exclusion in next requests
                                if "oldID" in product:
                                    self.excluded_product_ids.append(
                                        str(product["oldID"])
                                    )

                        except Exception as e:
                            print(f"   ⚠️ Error formatting product: {e}")
                            continue

        except Exception as e:
            print(f"   ❌ Error extracting products: {e}")

        return products

    def _format_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format raw product data into standardized structure."""
        try:
            # Extract basic product information
            product_id = str(product_data.get("oldID", ""))
            title = str(product_data.get("name", "")).strip()
            product_url = str(product_data.get("url", ""))

            if not title:
                return None

            # Extract price information
            price_data = cast(Dict[str, Any], product_data.get("price", {}))
            sale_price = str(price_data.get("text", ""))
            original_price = str(price_data.get("original", sale_price) or sale_price)
            discount_percentage = int(price_data.get("discountPercentage", 0))

            # Extract shop information
            shop_data = cast(Dict[str, Any], product_data.get("shop", {}))
            store_name = str(shop_data.get("name", ""))
            store_location = str(shop_data.get("city", ""))
            store_url = str(shop_data.get("url", ""))
            store_id = str(shop_data.get("oldID", ""))

            # Extract image information
            media_data = cast(Dict[str, Any], product_data.get("mediaURL", {}))
            image_url = str(
                media_data.get("image", "") or media_data.get("image300", "")
            )

            # Extract rating
            rating_raw = product_data.get("rating", 0)
            # Ensure rating is a number
            try:
                rating = float(rating_raw) if rating_raw else 0
            except (ValueError, TypeError):
                rating = 0

            # Make URLs absolute if needed
            if product_url and not str(product_url).startswith("http"):
                if str(product_url).startswith("/"):
                    product_url = f"https://www.tokopedia.com{product_url}"

            if store_url and not str(store_url).startswith("http"):
                if str(store_url).startswith("/"):
                    store_url = f"https://www.tokopedia.com{store_url}"
            elif not store_url and store_id:
                # Construct store URL from store ID
                store_url = f"https://www.tokopedia.com/store/{store_id}"

            if image_url and not str(image_url).startswith("http"):
                if str(image_url).startswith("//"):
                    image_url = f"https:{image_url}"
                elif str(image_url).startswith("/"):
                    image_url = f"https://www.tokopedia.com{image_url}"

            # Format product data
            formatted_product: Dict[str, Any] = {
                "Product ID": product_id,
                "Title": self.translator.translate(str(title)),
                "Sale Price": sale_price,
                "Original Price": original_price,
                "Discount (%)": discount_percentage,
                "Currency": "IDR",
                "Rating": rating if rating > 0 else None,
                "Orders Count": None,  # Not available in this API response
                "Store Name": self.translator.translate(str(store_name))
                if store_name
                else None,
                "Store ID": store_id if store_id else None,
                "Store URL": store_url if store_url else None,
                "Product URL": product_url,
                "Image URL": image_url,
                "Brand": self.config.get("brand", ""),
                "Location": self.translator.translate(str(store_location))
                if store_location
                else None,
                "Scraped At": datetime.now().isoformat(),
            }

            return formatted_product

        except Exception as e:
            print(f"   ⚠️ Error in _format_product: {e}")
            return None

    def scrape_products(self) -> List[Dict[str, Any]]:
        """Main method to scrape products using GraphQL API."""
        # Build search query
        keyword = self.config["keyword"]
        brand = self.config.get("brand", "")
        search_query = f"{brand} {keyword}".strip()

        max_pages = self.config.get("max_pages")
        max_products = self.config.get("max_products")
        delay = self.config.get("delay", 1.0)

        print(f"🚀 Starting Tokopedia GraphQL Scraper")
        print(f"🔍 Search Query: {search_query}")

        if max_products:
            print(f"🎯 Target: {max_products} products")
        elif max_pages:
            print(f"📄 Target: {max_pages} pages")
        else:
            print("♾️ Mode: Scrape all available products")

        print("=" * 60)

        page = 1
        start = 0

        try:
            while True:
                # Check limits
                if max_products and len(self.scraped_products) >= max_products:
                    print(f"   🎯 Reached target of {max_products} products")
                    break

                if max_pages and page > max_pages:
                    print(f"   📄 Reached target of {max_pages} pages")
                    break

                # Make GraphQL request
                response_data = self._make_graphql_request(search_query, page, start)

                if not response_data:
                    print(f"   ❌ Failed to get response for page {page}")
                    break

                # Extract products from response
                new_products = self._extract_products_from_response(response_data)

                if not new_products:
                    print(f"   📋 No more products found on page {page}")
                    break

                # Add products to collection
                for product in new_products:
                    if max_products and len(self.scraped_products) >= max_products:
                        break
                    self.scraped_products.append(product)
                    print(
                        f"   ✓ {len(self.scraped_products)}: {product.get('Title', 'Unknown')[:50]}..."
                    )

                print(
                    f"   📊 Page {page} completed: {len(new_products)} products found"
                )

                # Prepare for next page
                page += 1
                start += 60

                # Delay between requests
                if delay > 0:
                    print(f"   ⏳ Waiting {delay}s before next request...")
                    time.sleep(delay)

        except KeyboardInterrupt:
            print("\n🛑 Scraping interrupted by user")
        except Exception as e:
            print(f"\n❌ Scraping error: {e}")

        print("=" * 60)
        print(f"✅ Scraping completed!")
        print(f"📊 Total products scraped: {len(self.scraped_products)}")

        return self.scraped_products


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Tokopedia GraphQL Product Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --keyword "smartphone" --brand "iPhone" --max-products 100
  %(prog)s -k "laptop" -b "MacBook" --pages 3
  %(prog)s -k "headphone" -b "Sony" --delay 2.0
        """,
    )

    # Required arguments
    parser.add_argument("--keyword", "-k", required=True, help="Search keyword")
    parser.add_argument(
        "--brand", "-b", required=True, help="Brand name to associate with products"
    )

    # Scraping limits
    parser.add_argument(
        "--max-products", type=int, help="Maximum number of products to scrape"
    )
    parser.add_argument(
        "--max-pages",
        "--pages",
        type=int,
        help="Maximum pages to scrape (60 products per page)",
    )

    # Configuration
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )

    return parser


def main() -> None:
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()

    # Convert args to config dictionary
    config = {
        "keyword": args.keyword,
        "brand": args.brand,
        "max_products": args.max_products,
        "max_pages": args.max_pages,
        "delay": args.delay,
    }

    try:
        # Generate job ID for CLI execution
        job_id = str(uuid.uuid4())
        
        # Initialize path utils and job metadata
        path_utils = PathUtils()
        job_metadata = JobMetadata(
            job_id=job_id,
            parameters={
                "query": args.keyword,
                "brand": args.brand,
                "max_products": args.max_products,
                "max_pages": args.max_pages,
            }
        )
        
        print(f"\n🆔 Job ID: {job_id}")
        
        # Initialize and run scraper
        scraper = TokopediaGraphQLScraper(config)
        
        job_metadata.update_status(JobStatus.RUNNING)
        products = scraper.scrape_products()

        # Output results
        if products:
            print(f"\nTotal Products Scraped: {len(products)}")

            # Create job directories
            path_utils.ensure_job_dirs(job_id)
            json_dir = path_utils.get_job_json_dir(job_id)
            csv_dir = path_utils.get_job_csv_dir(job_id)
            
            # Save JSON
            json_file = json_dir / "results.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"\n💾 JSON results saved to: {json_file}")
            job_metadata.add_output_file("json/results.json")
            
            # Save CSV
            csv_file = csv_dir / "results.csv"
            csv_writer = TokopediaCSVWriter(csv_file)
            csv_writer.write_products(products)
            print(f"💾 CSV results saved to: {csv_file}")
            job_metadata.add_output_file("csv/results.csv")
            
            # Update job metadata
            job_metadata.set_results_summary(
                total_products=len(products),
                query=args.keyword,
                brand=args.brand,
                max_products=args.max_products,
                max_pages=args.max_pages,
            )
            job_metadata.update_status(JobStatus.COMPLETED)
            job_metadata.save(path_utils.get_job_metadata_path(job_id))
            
            print(f"📋 Job metadata saved to: {path_utils.get_job_metadata_path(job_id)}")
        else:
            print("\n⚠️ No products found.")
            job_metadata.update_status(JobStatus.FAILED, error_message="No products found")
            job_metadata.save(path_utils.get_job_metadata_path(job_id))
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        if 'job_id' in locals() and 'path_utils' in locals():
            job_metadata.update_status(JobStatus.FAILED, error_message=str(e))
            job_metadata.save(path_utils.get_job_metadata_path(job_id))
        sys.exit(1)


if __name__ == "__main__":
    main()
