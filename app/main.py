"""NEX Ledger FastAPI application."""

from fastapi import FastAPI

app = FastAPI(
    title="NEX Ledger",
    description="ICC Accounting System",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
