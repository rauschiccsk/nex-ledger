FROM python:3.12-slim

# Non-root user
RUN useradd -m -u 1000 icc && \
    mkdir -p /app && \
    chown -R icc:icc /app

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=icc:icc . .

USER icc

EXPOSE 9180

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9180/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9180"]
