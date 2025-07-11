# Grocery Genie - Multi-retailer grocery data scraper
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/costco data/walmart data/cvs data/publix data/other \
    && mkdir -p raw/walmart raw/publix \
    && mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV ENV=production

# Health check endpoint (we'll create a simple health check script)
COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python healthcheck.py

# Expose port for potential API endpoints
EXPOSE 8080

# Default command - can be overridden for different services
CMD ["python", "-c", "print('Grocery Genie container is ready. Use specific commands to run scrapers.')"]
