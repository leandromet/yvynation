# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for geospatial libraries
RUN apt-get update && apt-get install -y \
    git \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set Reflex environment variables for Cloud Run
ENV REFLEX_ENV=prod
ENV REFLEX_LOG_LEVEL=info
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run Reflex app with Gunicorn for Cloud Run
# First initialize the app, then run it
RUN reflex init || true

CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
