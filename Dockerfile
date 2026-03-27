FROM python:3.12-slim

# Metadata
LABEL maintainer="ICC s.r.o."
LABEL project="nex-ledger"

# Non-root user
RUN useradd -m -u 1000 appuser

# Working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Switch to non-root
USER appuser

# Expose port
EXPOSE 9180

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:9180/health', timeout=5)"

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9180"]
