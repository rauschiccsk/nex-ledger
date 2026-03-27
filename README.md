# NEX Ledger

ICC Accounting System

## Tech Stack
- Python 3.12
- FastAPI 0.115+
- SQLAlchemy 2.0 (sync)
- pg8000 (PostgreSQL driver)
- PostgreSQL 16

## Development Setup

### Prerequisites
- Python 3.12
- Poetry 1.8.3
- Docker + docker-compose

### Install dependencies
```bash
poetry install
```

### Run with Docker
```bash
docker-compose up -d
```

### Run tests
```bash
poetry run pytest -v --cov
```

### Lint
```bash
ruff check app/ tests/
```

## Environment Variables
See `.env.example` for required configuration.

## License
Proprietary — ICC s.r.o.
