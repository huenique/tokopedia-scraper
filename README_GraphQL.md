# Tokopedia GraphQL Scraper

A high-performance Python scraper that directly calls Tokopedia's GraphQL API instead of using browser automation. This approach is significantly faster, more reliable, and uses fewer resources than traditional web scraping methods.

## Features

- 🚀 **10x Faster**: Direct API calls without browser overhead
- 🎯 **More Reliable**: Direct access to structured data via GraphQL
- 💡 **Lower Resource Usage**: No browser process required
- 🔄 **Smart Pagination**: Handles large datasets with automatic pagination
- 🌍 **Translation Support**: Converts Indonesian terms to English
- 📊 **Structured Output**: Clean JSON data with consistent formatting
- 🛠️ **Easy to Use**: Simple command-line interface

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd tokopedia-scraper

# Install dependencies using uv (recommended)
uv add requests

# Or using pip
pip install requests
```

## Usage

### Basic Usage

```bash
# Scrape iPhone smartphones (20 products)
uv run python tokopedia_graphql.py --keyword "smartphone" --brand "iPhone" --max-products 20

# Scrape Samsung phones (5 pages ≈ 300 products)
uv run python tokopedia_graphql.py --keyword "smartphone" --brand "Samsung" --max-pages 5

# Scrape laptops with custom delay
uv run python tokopedia_graphql.py --keyword "laptop" --brand "MacBook" --max-products 50 --delay 2.0
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--keyword` | `-k` | Search keyword (required) | - |
| `--brand` | `-b` | Brand name to filter (required) | - |
| `--max-products` | - | Maximum number of products to scrape | Unlimited |
| `--max-pages` | - | Maximum pages to scrape (60 products/page) | Unlimited |
| `--delay` | - | Delay between requests (seconds) | 1.0 |

### Examples

```bash
# Quick test with 10 products
uv run python tokopedia_graphql.py -k "smartphone" -b "Xiaomi" --max-products 10

# Comprehensive scrape (500+ products)
uv run python tokopedia_graphql.py -k "smartphone" -b "Samsung" --max-pages 10

# Slow and steady (respectful scraping)
uv run python tokopedia_graphql.py -k "laptop" -b "Lenovo" --max-products 100 --delay 3.0
```

## Output

### JSON Structure

Each scraped product contains the following fields:

```json
{
  "Product ID": "16187355157",
  "Title": "Apple iPhone 15 PRO/15 PRO MAX 128GB Complete Set Second Hand Original",
  "Sale Price": "Rp1.850.000",
  "Original Price": "Rp2.312.500", 
  "Discount (%)": 20,
  "Currency": "IDR",
  "Rating": 4.6,
  "Orders Count": null,
  "Store Name": "sofiney",
  "Store ID": "18377743",
  "Store URL": "https://www.tokopedia.com/sofiney",
  "Product URL": "https://www.tokopedia.com/sofiney/product-url",
  "Image URL": "https://images.tokopedia.net/img/cache/200-square/image.jpg",
  "Brand": "iPhone",
  "Location": "Jakarta Utara", 
  "Scraped At": "2025-08-19T09:55:46.817420"
}
```

### File Output

Results are automatically saved to `results/tokopedia_{brand}_{date}_{timestamp}.json`

Example: `results/tokopedia_iphone_20250819_1755568547.json`

## API Analysis

### GraphQL Endpoint

The scraper makes requests to Tokopedia's official GraphQL API:

```bash
POST https://gql.tokopedia.com/graphql/SearchProductV5Query
```

### Key Features

1. **Pagination Support**: Automatically handles multiple pages with proper offset management
2. **Duplicate Prevention**: Uses `minus_ids` parameter to exclude already seen products
3. **Session Consistency**: Maintains `search_id` across paginated requests
4. **Realistic Headers**: Mimics browser behavior with proper headers and device IDs

### Request Flow

```txt
1. Initial Request (page=1, start=0, rows=60)
2. Extract products + search_id + product_ids
3. Next Request (page=2, start=60, minus_ids=previous_ids) 
4. Repeat until target reached or no more products
```

## Performance Comparison

| Metric | GraphQL API | Browser Automation |
|--------|-------------|-------------------|
| Speed | ~2-5 seconds | ~30-60 seconds |
| Memory Usage | ~50MB | ~500MB+ |
| Browser Required | ❌ No | ✅ Yes |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Maintenance | Easy | Complex |
| Deployment | Simple | Requires browser |

### Speed Test Results

```bash
# Test: 20 iPhone products

GraphQL API Approach:
✅ Duration: 3.2 seconds
📊 Products: 20 products  
💾 Memory: Low (HTTP only)

Browser Automation:
✅ Duration: 47.8 seconds  
📊 Products: 20 products
💾 Memory: High (Browser + Node.js)

🏆 Result: 93.3% faster with GraphQL!
```

## Translation Features

The scraper automatically translates Indonesian terms to English:

- **Product Terms**: Bekas → Used, Garansi → Warranty, etc.
- **Locations**: Kab. → Regency, Kota → City
- **Store Terms**: Official Distributor terms and common phrases

## Technical Details

### Headers & Authentication

The scraper uses realistic browser headers:

- User-Agent: Chrome/Edge browser simulation
- Device IDs: Random but consistent session IDs
- Tokopedia-specific headers: `x-source`, `x-device`, etc.

### Error Handling

- Network timeout protection (30 seconds per request)
- Retry logic for failed requests  
- Graceful handling of rate limits
- Product formatting error recovery

### Data Validation

- Ensures required fields are present
- Validates URLs and makes them absolute
- Handles missing or malformed price data
- Converts ratings to numeric values

## Limitations

1. **Rate Limiting**: Tokopedia may rate limit high-frequency requests
2. **API Changes**: GraphQL schema changes could break the scraper
3. **Product Availability**: Some products may become unavailable during scraping
4. **Geographic Restrictions**: Results may vary by location/IP

## Best Practices

1. **Respectful Scraping**: Use delays (`--delay`) to avoid overwhelming servers
2. **Reasonable Limits**: Don't scrape more data than you need  
3. **Error Handling**: Check logs for failed requests or malformed data
4. **Data Validation**: Verify scraped data quality before use
5. **Legal Compliance**: Ensure usage complies with Tokopedia's terms of service

## Troubleshooting

### Common Issues

#### No products found

```bash
# Try different search terms or check if products exist
uv run python tokopedia_graphql.py -k "mobile phone" -b "Apple" --max-products 5
```

#### Request timeouts

```bash  
# Increase delay between requests
uv run python tokopedia_graphql.py -k "smartphone" -b "Samsung" --delay 2.0
```

#### Rate limiting

```bash
# Reduce request frequency
uv run python tokopedia_graphql.py -k "laptop" -b "Dell" --delay 5.0 --max-products 10
```

### Debug Mode

For debugging, examine the raw output:

```bash
uv run python tokopedia_graphql.py -k "smartphone" -b "iPhone" --max-products 3 > debug.log 2>&1
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with detailed description

## License

This project is for educational and research purposes. Please ensure compliance with Tokopedia's terms of service and applicable laws when using this scraper.

---

## Alternative: Browser Automation

For comparison, the repository also includes `tokopedia_cli.py` which uses browser automation (Crawlee/Playwright). While slower and more resource-intensive, it may be useful for:

- Visual debugging and development
- Handling complex JavaScript-rendered content
- Scenarios where the GraphQL API is unavailable

Usage:

```bash
uv run python tokopedia_cli.py --keyword "smartphone" --brand "iPhone" --max-pages 2
```

---

**Recommendation**: Use the GraphQL scraper (`tokopedia_graphql.py`) for production use due to its superior performance and reliability.
