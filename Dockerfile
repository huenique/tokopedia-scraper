# Dockerfile for Tokopedia Scraper Service
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libu2f-udev \
    libvulkan1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python dependency management
RUN pip install uv

# Create non-root user for security
RUN groupadd -r scraper && useradd -r -g scraper scraper

# Set working directory
WORKDIR /app

# Copy project files
COPY --chown=scraper:scraper . .

# Install Python dependencies
RUN uv sync --frozen

# Install playwright browsers
RUN uv run python -m playwright install chromium
RUN uv run python -m playwright install-deps chromium

# Switch to non-root user
USER scraper

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=8002

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start the service
CMD ["uv", "run", "uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8002"]
