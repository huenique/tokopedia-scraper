# Tokopedia Scraper REST API

This document describes the REST API endpoints for the Tokopedia product scraper service.

## Base URL

```bash
http://localhost:8002
```

## Quick Start

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Start the API server:

   ```bash
   ./start_api.sh
   # or manually:
   uv run uvicorn api_service:app --host 0.0.0.0 --port 8002 --reload
   ```

3. View API documentation:
   - Interactive docs: <http://localhost:8002/docs>
   - OpenAPI spec: <http://localhost:8002/openapi.json>

## API Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the service.

### Start Scraping Job

```http
POST /scrape/search
```

Starts a new product scraping job using GraphQL API.

**Request Body:**

```json
{
  "query": "smartphone",          // Required: Search query
  "brand": "iPhone",             // Optional: Brand filter
  "max_products": 100,           // Maximum products (1-1000)
  "pages": 3,                    // Optional: Number of pages (1-50)
  "output_format": "json"        // Output format: json|csv
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Scraping job started successfully"
}
```

### Check Job Status

```http
GET /scrape/status/{job_id}
```

Returns the current status of a scraping job.

### Get Job Results

```http
GET /scrape/results/{job_id}
```

Returns the results of a completed scraping job with Indonesian terms translated to English.

### List All Jobs

```http
GET /scrape/jobs
```

Returns a list of all scraping jobs.

### Delete Job

```http
DELETE /scrape/jobs/{job_id}
```

Cancels/deletes a scraping job and its results.

## Features

- **GraphQL API Integration**: Uses Tokopedia's GraphQL API for faster, more efficient scraping
- **Translation Support**: Automatically translates Indonesian product terms to English
- **Flexible Search**: Search by keyword with optional brand filtering
- **High Performance**: No browser automation needed, direct API calls
