# Multi-stage build for production-ready image
FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Set Poetry config — install into system site-packages
RUN poetry config virtualenvs.create false

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install production dependencies only (no root package yet)
RUN poetry install --no-root --only=main

# Final stage
FROM python:3.12-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash nexledger

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=nexledger:nexledger app/ ./app/
COPY --chown=nexledger:nexledger alembic/ ./alembic/
COPY --chown=nexledger:nexledger alembic.ini pyproject.toml poetry.lock ./

# Switch to non-root user
USER nexledger

# Health check (port 9180 — ICC Port Registry)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9180/health || exit 1

# Expose API port (ICC Port Registry)
EXPOSE 9180

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9180"]
