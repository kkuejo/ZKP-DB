# Single-stage build for ZKP-DB backend
FROM python:3.11-slim

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    libgomp1 \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install snarkjs globally
RUN npm install -g snarkjs

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy circuits and keys (required for ZKP)
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

# Start the application
WORKDIR /app/backend
CMD gunicorn provider_api:app --bind 0.0.0.0:${PORT} --timeout 180 --workers 1 --worker-class sync --log-level info
