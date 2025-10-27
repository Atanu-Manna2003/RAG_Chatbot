FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - Combine commands for smaller layers
# - Clean up temporary files to minimize image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Copy and install Python dependencies first for caching benefits
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only necessary application code (avoids copying local venvs, etc.)
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY storage/ ./storage/
COPY .env ./
COPY frontend/ ./frontend/

# Create directories needed at runtime
RUN mkdir -p /app/storage/documents /app/storage/vector_store /app/logs

# Set environment variables for consistency
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose app port
EXPOSE 8000

# Health check endpoint (ensure /health exists)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command to start the app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
