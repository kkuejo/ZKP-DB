# Multi-stage build for memory-efficient ZKP-DB backend
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --prefix=/install -r backend/requirements.txt

# Runtime stage - minimal image
FROM python:3.11-slim

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    nodejs \
    npm \
    && npm install -g snarkjs \
    && apt-get remove -y npm \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.npm

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ ./backend/
COPY circuits/ ./circuits/
COPY keys/ ./keys/

# Create directory for secret contexts
RUN mkdir -p /app/backend/secret_contexts && chmod 755 /app/backend/secret_contexts

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check (using curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Start the application with memory-optimized settings
WORKDIR /app/backend
CMD gunicorn provider_api:app \
    --bind 0.0.0.0:${PORT} \
    --timeout 180 \
    --workers 1 \
    --threads 2 \
    --worker-class gthread \
    --max-requests 100 \
    --max-requests-jitter 10 \
    --log-level info
