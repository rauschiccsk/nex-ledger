# NEX Ledger Backend

FastAPI backend pre NEX Ledger — multi-tenant accounting systém.

## Development

```bash
poetry install
poetry run uvicorn app.main:app --reload --port 9180
```

## Docker

```bash
docker build -t nex-ledger-backend .
docker run -p 9180:9180 --env-file .env nex-ledger-backend
```

## Endpoints

- `GET /health` — Health check
