FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 ledger && \
    mkdir -p /app && \
    chown ledger:ledger /app

WORKDIR /app

# Install dependencies
COPY --chown=ledger:ledger requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=ledger:ledger app/ ./app/

USER ledger

EXPOSE 9180

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9180/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9180"]
