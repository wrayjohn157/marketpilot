# Multi-stage Dockerfile for Market7 Trading System
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir \
    gunicorn \
    supervisor \
    psutil \
    prometheus-client \
    sentry-sdk

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data models cache backups output
RUN mkdir -p logs/{trading,ml,indicators,dca}
RUN mkdir -p data/{historical,realtime,backtest}
RUN mkdir -p models/{safu,recovery,confidence,dca_spend,trade_success}
RUN mkdir -p cache/{indicators,ml,redis}
RUN mkdir -p backups/{config,models,data}
RUN mkdir -p output/{trades,reports,logs}

# Set permissions
RUN chown -R appuser:appuser /app
RUN chmod -R 755 /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 health_check.py

# Default command
CMD ["python3", "main_orchestrator.py"]
