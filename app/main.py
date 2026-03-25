from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NEX Ledger API", version="0.1.0")

# CORS pre frontend (port 9181)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9181", "http://100.107.134.104:9181"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
