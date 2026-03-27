"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="NEX Ledger",
    description="Financial ledger system for NEX Automat",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and Docker healthcheck."""
    return {"status": "ok"}
