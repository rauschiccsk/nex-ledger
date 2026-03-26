# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 ledger && \
    mkdir -p /app && \
    chown -R ledger:ledger /app

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=ledger:ledger . .

# Switch to non-root user
USER ledger

# Expose port
EXPOSE 9180

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9180/health').raise_for_status()"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9180"]
