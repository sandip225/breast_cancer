# Backend Dockerfile for Docker Compose
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with extended timeout
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy all application code
COPY . .

# Ensure models directory exists with proper permissions
RUN mkdir -p /app/models && chmod 755 /app/models

# Make startup script executable
RUN chmod +x /app/startup.sh

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Run application using startup script
CMD ["/app/startup.sh"]
