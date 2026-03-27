"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="NEX Ledger",
    description="Účtovný systém pre ICC s.r.o.",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )
