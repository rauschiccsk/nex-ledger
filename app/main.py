"""
NEX Ledger — Main FastAPI application.
Port: 9180 (ICC Port Registry)
"""

from datetime import UTC, datetime

from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Accounting & invoicing system for ICC",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }
