#!/bin/bash
"""
Tokopedia Scraper API Server Startup Script
==========================================

Starts the Tokopedia scraper REST API service on port 8002.
"""

# Install dependencies if needed
echo "Installing dependencies..."
uv sync

# Start the API server
echo "Starting Tokopedia Scraper API on http://localhost:8002"
echo "API Documentation available at http://localhost:8002/docs"
uv run uvicorn api_service:app --host 0.0.0.0 --port 8002 --reload
