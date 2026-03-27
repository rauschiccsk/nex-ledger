# NEX Ledger

Financial ledger system for NEX Automat — multi-tenant accounting with double-entry bookkeeping.

## Tech Stack
- Python 3.12
- FastAPI 0.115+
- SQLAlchemy 2.0 (sync, pg8000 driver)
- PostgreSQL 16
- Docker

## Development

### Setup
```bash
poetry install
cp .env.example .env
docker-compose up -d postgres
poetry run pytest
```

### Run
```bash
poetry run uvicorn app.main:app --reload --port 9180
```

### Docker
```bash
docker-compose up --build
```

## Port Assignment
- **9180** — NEX Ledger API (ICC Port Registry)
- **9181** — NEX Ledger Web (ICC Port Registry)
