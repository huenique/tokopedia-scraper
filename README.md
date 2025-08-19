# Tokopedia Scrapers

High-performance Python scrapers for Tokopedia product data with both GraphQL API and browser automation approaches.

## 🚀 **Recommended: GraphQL Scraper**

The **GraphQL scraper** (`tokopedia_graphql.py`) is our **recommended approach** that directly calls Tokopedia's API for superior performance:

- ⚡ **10x Faster**: 3 seconds vs 45+ seconds
- 🎯 **More Reliable**: No browser crashes or timeouts  
- 💡 **Lower Resources**: No browser process overhead
- 🔄 **Smart Pagination**: Handles unlimited products efficiently
- 🌍 **Translation**: Indonesian → English terms
- 📊 **Clean Output**: Structured JSON with consistent formatting

## 📦 Installation

```bash
# Clone repository
git clone <repository-url>
cd tokopedia-scraper

# Install dependencies (uv recommended)
uv install

# Or using pip
pip install -r requirements.txt
```

## 🎯 Quick Start (GraphQL)

```bash
# Scrape iPhone smartphones (50 products)
uv run python tokopedia_graphql.py --keyword "smartphone" --brand "iPhone" --max-products 50

# Scrape Samsung phones (3 pages ≈ 180 products)  
uv run python tokopedia_graphql.py -k "smartphone" -b "Samsung" --max-pages 3

# Scrape with custom delay (respectful scraping)
uv run python tokopedia_graphql.py -k "laptop" -b "MacBook" --max-products 100 --delay 2.0
```

## 📋 Available Scrapers

### 1. **GraphQL Scraper** (Recommended) ⭐

**File**: `tokopedia_graphql.py`  
**Method**: Direct GraphQL API calls  
**Speed**: ~3 seconds per 60 products  
**Reliability**: Excellent  

```bash
# Basic usage
uv run python tokopedia_graphql.py --keyword "smartphone" --brand "iPhone" --max-products 50

# All options
uv run python tokopedia_graphql.py \
  --keyword "laptop" \
  --brand "MacBook" \
  --max-products 200 \
  --delay 1.5
```

**Options:**

- `--keyword` / `-k`: Search keyword (required)
- `--brand` / `-b`: Brand filter (required)
- `--max-products`: Limit number of products
- `--max-pages`: Limit pages (60 products/page)
- `--delay`: Request delay in seconds (default: 1.0)

### 2. **Browser Scraper** (Legacy)

**File**: `tokopedia_cli.py`  
**Method**: Browser automation with Crawlee  
**Speed**: ~45+ seconds per 60 products  
**Reliability**: Moderate (browser dependent)

```bash
# Basic usage
uv run python tokopedia_cli.py --keyword "smartphone" --brand "iPhone" --max-products 50
```

## 📊 Output Format

Both scrapers produce identical JSON output:

```json
{
  "Product ID": "16187355157",
  "Title": "Apple iPhone 15 PRO 128GB Complete Set Original",
  "Sale Price": "Rp1.850.000",
  "Original Price": "Rp2.312.500",
  "Discount (%)": 20,
  "Currency": "IDR", 
  "Rating": 4.6,
  "Orders Count": null,
  "Store Name": "Premium Store",
  "Store ID": "18377743",
  "Store URL": "https://www.tokopedia.com/premium-store",
  "Product URL": "https://www.tokopedia.com/premium-store/iphone-15-pro",
  "Image URL": "https://images.tokopedia.net/img/cache/200-square/image.jpg",
  "Brand": "iPhone",
  "Location": "Jakarta Utara",
  "Scraped At": "2025-08-19T09:55:46.817420"
}
```

Results are saved to: `results/tokopedia_{brand}_{date}_{timestamp}.json`

## ⚡ Performance Comparison

| Metric | GraphQL Scraper | Browser Scraper |
|--------|-----------------|-----------------|
| **Speed** | ~3 seconds/60 products | ~45+ seconds/60 products |
| **Reliability** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Moderate |
| **Resources** | Low CPU/Memory | High CPU/Memory |
| **Scalability** | Unlimited pages | Limited by browser |
| **Maintenance** | Minimal | Browser updates needed |

## 🔧 Advanced Usage

### Pagination Control

```bash
# Scrape exactly 100 products
uv run python tokopedia_graphql.py -k "smartphone" -b "Samsung" --max-products 100

# Scrape 5 pages (≈300 products)
uv run python tokopedia_graphql.py -k "smartphone" -b "iPhone" --max-pages 5

# Unlimited scraping (until no more results)
uv run python tokopedia_graphql.py -k "laptop" -b "Asus"
```

### Rate Limiting & Politeness

```bash
# Slow and respectful (3-second delays)
uv run python tokopedia_graphql.py -k "smartphone" -b "Oppo" --max-products 200 --delay 3.0

# Fast but respectful (1-second delays) - default
uv run python tokopedia_graphql.py -k "smartphone" -b "Vivo" --max-products 100
```

### Brand-Specific Scraping

```bash
# Popular smartphone brands
uv run python tokopedia_graphql.py -k "smartphone" -b "iPhone" --max-products 100
uv run python tokopedia_graphql.py -k "smartphone" -b "Samsung" --max-products 100  
uv run python tokopedia_graphql.py -k "smartphone" -b "Xiaomi" --max-products 100

# Laptop brands
uv run python tokopedia_graphql.py -k "laptop" -b "MacBook" --max-products 50
uv run python tokopedia_graphql.py -k "laptop" -b "ThinkPad" --max-products 50
uv run python tokopedia_graphql.py -k "laptop" -b "Asus" --max-products 50
```

## 🏗️ Project Structure

```bash
tokopedia-scraper/
├── tokopedia_graphql.py     # ⭐ GraphQL scraper (recommended)
├── tokopedia_cli.py         # Browser scraper (legacy)
├── comparison_test.py       # Performance comparison tool
├── README_GraphQL.md        # Detailed GraphQL documentation
├── pyproject.toml          # Project dependencies
├── results/                # Scraped data output
│   ├── tokopedia_iphone_*.json
│   ├── tokopedia_samsung_*.json
│   └── ...
└── storage/                # Browser scraper cache
```

## 🛠️ Development

### Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "crawlee[all]>=0.6.12",    # Browser scraper
    "requests>=2.31.0",        # GraphQL scraper
]
```

### Testing

```bash
# Quick test (10 products each)
uv run python tokopedia_graphql.py -k "smartphone" -b "iPhone" --max-products 10
uv run python tokopedia_cli.py -k "smartphone" -b "iPhone" --max-products 10

# Performance comparison
uv run python comparison_test.py
```

## 🌟 Features

### GraphQL Scraper Features

- ✅ **Fast Pagination**: 60 products per page with smart offset management
- ✅ **Duplicate Prevention**: Tracks scraped products across pages
- ✅ **Translation Engine**: Indonesian → English product terms
- ✅ **Error Handling**: Robust retry logic and graceful failures
- ✅ **Rate Limiting**: Configurable delays between requests
- ✅ **Session Management**: Maintains consistent API sessions
- ✅ **Clean Data**: Structured output with proper typing

### Browser Scraper Features

- ✅ **Full Browser**: Handles JavaScript and dynamic content
- ✅ **Visual Debugging**: Can see what's happening during scraping
- ✅ **Fallback Option**: Works when API access is restricted

## 🚨 Recommendations

### Use GraphQL Scraper When

- ⭐ **Performance matters** (10x faster)
- ⭐ **Scraping large datasets** (100+ products)
- ⭐ **Running automated workflows** (more reliable)
- ⭐ **Limited resources** (lower CPU/memory usage)

### Use Browser Scraper When

- 🔄 GraphQL scraper is blocked or rate-limited
- 🔍 Need to debug what users actually see
- 📸 Require screenshot capabilities
- 🧪 Testing different scraping strategies

## 📄 Documentation

- **[README_GraphQL.md](README_GraphQL.md)**: Detailed GraphQL scraper documentation
- **[API Analysis](README_GraphQL.md#api-analysis)**: How the GraphQL endpoints work
- **[Troubleshooting](README_GraphQL.md#troubleshooting)**: Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test with both scrapers
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📈 Roadmap

- [ ] **Multi-threading support** for GraphQL scraper
- [ ] **Additional e-commerce platforms** (Shopee, Lazada)
- [ ] **Real-time price monitoring**
- [ ] **Data export formats** (CSV, Excel)
- [ ] **API rate limit auto-detection**
- [ ] **Proxy rotation support**

## ⚠️ Legal Notice

This tool is for educational and research purposes only. Please respect Tokopedia's robots.txt and terms of service. Use reasonable delays between requests and avoid overwhelming their servers.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

⭐ **Tip**: Start with the GraphQL scraper for best performance, and fall back to the browser scraper only if needed!
