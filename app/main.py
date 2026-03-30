"""
NEX Ledger — Main FastAPI application.
Port: 9180 (ICC Port Registry)
"""

from datetime import UTC, datetime

from fastapi import FastAPI

from app.api.v1 import account_types, business_partners, tax_rates
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Accounting & invoicing system for ICC",
    version="0.1.0",
    debug=settings.DEBUG,
)


app.include_router(
    account_types.router,
    prefix="/api/v1/account-types",
    tags=["account-types"],
)

app.include_router(
    business_partners.router,
    prefix="/api/v1/business-partners",
    tags=["business-partners"],
)

app.include_router(
    tax_rates.router,
    prefix="/api/v1/tax-rates",
    tags=["tax-rates"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }
