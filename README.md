# Tokopedia Scrapers

High-performance Python scrapers for Tokopedia product data with both GraphQL API and browser automation approaches.

## 🚀 **Recommended: GraphQL Scraper**

The **GraphQL scraper** (`tokopedia_graphql.py`) is our **recommended approach** that directly calls Tokopedia's API for superior performance:

- ⚡ **2-15x Faster**: ~2-5 seconds vs ~30-60 seconds per 60 products
- 🎯 **More Reliable**: No browser crashes or timeouts  
- 💡 **Lower Resources**: No browser process overhead (~50MB vs ~500MB+)
- 🔄 **Smart Pagination**: Handles unlimited products efficiently
- 🌍 **Translation**: Indonesian → English terms
- 📊 **Dual Output**: Structured JSON and CSV (unified template format)

## 📦 Installation

**Requirements**: Python 3.13+ (as specified in `pyproject.toml`)

```bash
# Clone repository
git clone <repository-url>
cd tokopedia-scraper

# Install dependencies (uv recommended)
uv sync

# Or using pip (requires requirements.txt to be generated)
pip install crawlee[all] requests fastapi pydantic uvicorn[standard]
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

**Note:** Each run generates a unique Job ID and saves results to `results/jobs/{job_id}/`

## 📋 Available Scrapers

### 1. **GraphQL Scraper** (Recommended) ⭐

**File**: `tokopedia_graphql.py`  
**Method**: Direct GraphQL API calls  
**Speed**: ~2-5 seconds per 60 products  
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

#### Options (GraphQL Scraper)

- `--keyword` / `-k`: Search keyword (required)
- `--brand` / `-b`: Brand filter (required)
- `--max-products`: Limit number of products
- `--max-pages`: Limit pages (60 products/page)
- `--delay`: Request delay in seconds (default: 1.0)

### 2. **Browser Scraper** (Legacy)

**File**: `tokopedia_cli.py`  
**Method**: Browser automation with Crawlee  
**Speed**: ~30-60 seconds per variable number of products  
**Reliability**: Moderate (browser dependent)

```bash
# Basic usage
uv run python tokopedia_cli.py --keyword "smartphone" --brand "iPhone"

# With page limit
uv run python tokopedia_cli.py --keyword "smartphone" --brand "iPhone" --max-pages 3
```

#### Options (Browser Scraper)

- `--keyword` / `-k`: Search keyword (required)
- `--brand` / `-b`: Brand filter (required)  
- `--max-pages`: Limit pages to scrape (default: infinite scroll)
- `--delay`: Delay between scroll actions in seconds (default: 2.0)

**Note**: The browser scraper does NOT have a `--max-products` option and uses infinite scrolling by default.

### 3. **REST API Service** (Production Ready) 🚀

Tokopedia scraper provides two API implementations:

1. **Standard API** (`api/main.py`) - Aligned with other scrapers using `/api/v1/jobs` pattern
2. **Legacy API** (`api_service.py`) - Original API with `/scrape/*` endpoints

#### Starting the API Server

```bash
# Using the startup script (Legacy API on port 8002)
./start_api.sh

# Or manually - Legacy API
uv run uvicorn api_service:app --host 0.0.0.0 --port 8002 --reload

# Or manually - Standard API (on port 8003)
uv run uvicorn api.main:app --host 0.0.0.0 --port 8003 --reload
```

The API will be available at:

- **Legacy API**: <http://localhost:8002> (uses GraphQL scraper internally)
- **Standard API**: <http://localhost:8003>
- **Interactive Docs**: <http://localhost:8002/docs> or <http://localhost:8003/docs>
- **OpenAPI Spec**: <http://localhost:8002/openapi.json> or <http://localhost:8003/openapi.json>

#### Standard API Endpoints (`/api/v1/jobs`)

#### Health Check (Standard API)

```bash
curl http://localhost:8003/health
```

#### Create Scraping Job (Standard API)

```bash
curl -X POST "http://localhost:8003/api/v1/jobs?query=smartphone&brand=iPhone&max_products=100"
```

#### Get Job Status (Standard API)

```bash
curl http://localhost:8003/api/v1/jobs/{job_id}
```

#### Get Job Results (with pagination, Standard API)

```bash
curl "http://localhost:8003/api/v1/jobs/{job_id}/results?page=1&page_size=50"
```

#### List All Jobs (Standard API)

```bash
curl http://localhost:8003/api/v1/jobs
```

#### Delete Job (Standard API)

```bash
curl -X DELETE http://localhost:8003/api/v1/jobs/{job_id}
```

#### Legacy API Endpoints (`/scrape/*`)

#### Create Scraping Job (Legacy API)

```bash
curl -X POST "http://localhost:8002/scrape/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "smartphone",
    "brand": "iPhone", 
    "max_products": 100,
    "output_format": "json"
  }'
```

#### Check Job Status (Legacy API)

```bash
curl "http://localhost:8002/scrape/status/{job_id}"
```

#### Get Results (Legacy API)

```bash
curl "http://localhost:8002/scrape/results/{job_id}"
```

#### List All Jobs (Legacy API)

```bash
curl "http://localhost:8002/scrape/jobs"
```

#### Delete Job (Legacy API)

```bash
curl -X DELETE "http://localhost:8002/scrape/jobs/{job_id}"
```

#### Features

- ✅ **Asynchronous job processing** with status tracking
- ✅ **RESTful endpoints** for starting, monitoring, and retrieving scrapes
- ✅ **Job management** with unique job IDs
- ✅ **Error handling** and progress tracking
- ✅ **Interactive API documentation** (Swagger UI)
- ✅ **Uses GraphQL scraper** internally for best performance

See [API_GUIDE.md](API_GUIDE.md) for complete API documentation.

## 📊 Output Format

Both scrapers produce **JSON and CSV** output:

### JSON Format

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

### CSV Format

CSV files follow the **unified template format** for uploading listings with these columns:

```txt
Listing Title*, Listings URL*, Image URL*, Marketplace*, Price*, Shipping, 
Units Available, Item Number, Brand, ASIN, UPC, Walmart ID, Seller's Name*, 
Seller's URL*, Seller's Business Name, Seller's Address, Seller's Email, 
Seller's Phone Number
```

#### Output Files

Both CLI and API modes use the **same job-based structure**:

- `results/jobs/{job_id}/json/results.json`
- `results/jobs/{job_id}/csv/results.csv`
- `results/jobs/{job_id}/job_metadata.json`

The CLI will display the job ID when starting, allowing you to track and locate the results:

```bash
🆔 Job ID: e18408a4-9e9d-4735-a1a9-4240f48bb698
```

## 🔄 Utilities

### CSV Regeneration

If you have existing job results with only JSON files, you can regenerate CSV files:

```bash
# Regenerate CSV files for all jobs that have JSON but no CSV
uv run python regenerate_csv.py
```

This utility will:

- Scan all job directories in `results/jobs/`
- Find jobs with JSON results but no CSV
- Generate CSV files matching the unified template format
- Skip jobs that already have CSV files

## ⚡ Performance Comparison

| Metric | GraphQL Scraper | Browser Scraper |
|--------|-----------------|-----------------|
| **Speed** | ~2-5 seconds/60 products | ~30-60 seconds/60 products |
| **Reliability** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Moderate |
| **Resources** | Low CPU/Memory (~50MB) | High CPU/Memory (~500MB+) |
| **Scalability** | Unlimited pages | Limited by browser stability |
| **Maintenance** | Minimal | Browser updates needed |
| **Browser Required** | ❌ No | ✅ Yes |

## 🔧 Advanced Usage

### Pagination Control (GraphQL Scraper)

```bash
# Scrape exactly 100 products
uv run python tokopedia_graphql.py -k "smartphone" -b "Samsung" --max-products 100

# Scrape 5 pages (≈300 products)
uv run python tokopedia_graphql.py -k "smartphone" -b "iPhone" --max-pages 5

# Unlimited scraping (until no more results)
uv run python tokopedia_graphql.py -k "laptop" -b "Asus"
```

### Browser Scraper Usage

```bash
# Infinite scroll (default behavior)
uv run python tokopedia_cli.py -k "smartphone" -b "Samsung"

# Limited pages (approximate 60 products per "page")
uv run python tokopedia_cli.py -k "smartphone" -b "iPhone" --max-pages 3

# Custom scroll delay
uv run python tokopedia_cli.py -k "laptop" -b "MacBook" --max-pages 2 --delay 3.0
```

### Rate Limiting & Politeness

#### GraphQL Scraper

```bash
# Slow and respectful (3-second delays)
uv run python tokopedia_graphql.py -k "smartphone" -b "Oppo" --max-products 200 --delay 3.0

# Fast but respectful (1-second delays) - default
uv run python tokopedia_graphql.py -k "smartphone" -b "Vivo" --max-products 100
```

#### Browser Scraper

```bash
# Slow scrolling (3-second delays between scrolls)
uv run python tokopedia_cli.py -k "smartphone" -b "Oppo" --max-pages 5 --delay 3.0

# Default scrolling (2-second delays) - default
uv run python tokopedia_cli.py -k "smartphone" -b "Vivo" --max-pages 3
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
├── api_service.py          # REST API service
├── start_api.sh            # API server startup script  
├── API_GUIDE.md            # REST API documentation
├── README_GraphQL.md        # Detailed GraphQL documentation
├── pyproject.toml          # Project dependencies (uv format)
├── results/                # Scraped data output
│   ├── tokopedia_iphone_*.json
│   ├── tokopedia_samsung_*.json
│   └── ...
└── storage/                # Browser scraper cache (Crawlee)
```

## 🛠️ Development

### Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "crawlee[all]>=0.6.12",    # Browser scraper
    "requests>=2.32.5",        # GraphQL scraper  
    "fastapi>=0.104.1",        # REST API service
    "pydantic>=2.5.0",         # Data validation
    "uvicorn[standard]>=0.35.0", # ASGI server
]
```

### Testing

```bash
# Quick test (10 products each)
uv run python tokopedia_graphql.py -k "smartphone" -b "iPhone" --max-products 10
uv run python tokopedia_cli.py -k "smartphone" -b "iPhone" --max-pages 1

# Test REST API
./start_api.sh
# Then visit http://localhost:8002/docs
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

- ⭐ **Performance matters** (2-15x faster depending on data size)
- ⭐ **Scraping large datasets** (100+ products)
- ⭐ **Running automated workflows** (more reliable)
- ⭐ **Limited resources** (lower CPU/memory usage)
- ⭐ **Production environments** (better error handling)

### Use Browser Scraper When

- 🔄 GraphQL scraper is blocked or rate-limited
- 🔍 Need to debug what users actually see
- 📸 Require screenshot capabilities for visual verification
- 🧪 Testing different scraping strategies
- 🎯 Need to scrape specific UI elements not in the API

### Use REST API Service When

- 🌐 **Integrating with web applications** or other services
- 📊 **Building dashboards** or monitoring tools
- 🔄 **Need asynchronous processing** with job tracking
- 🏢 **Production deployments** requiring API endpoints
- 📈 **Scaling scraping operations** across multiple consumers

## 📄 Documentation

- **[README_GraphQL.md](README_GraphQL.md)**: Detailed GraphQL scraper documentation with performance benchmarks
- **[API_GUIDE.md](API_GUIDE.md)**: REST API service documentation and usage examples
- **[start_api.sh](start_api.sh)**: Script to start the REST API server

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
- [x] **REST API service** (implemented in `api_service.py`)
- [x] **FastAPI integration** with job management

## ⚠️ Legal Notice

This tool is for educational and research purposes only. Please respect Tokopedia's robots.txt and terms of service. Use reasonable delays between requests and avoid overwhelming their servers.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

⭐ **Tip**: Start with the GraphQL scraper for best performance, and fall back to the browser scraper only if needed!
