# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export requirements
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Copy requirements from builder
COPY --from=builder /build/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 9180

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9180/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9180"]
