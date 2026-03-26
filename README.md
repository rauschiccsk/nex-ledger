# NEX Ledger

Accounting module for NEX ecosystem. Double-entry bookkeeping, Slovak legislation.

**Status:** Initializing — clean slate after crash test audit.

## Ports

- Backend: 9180
- Frontend: 9181

## Design

See `/home/icc/knowledge/projects/nex-ledger/DESIGN.md`

## Project Structure

```
nex-ledger/
├── app/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration (Pydantic BaseSettings)
│   ├── database.py          # SQLAlchemy engine (pg8000 driver)
│   └── models/              # SQLAlchemy models
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (PostgreSQL)
│   └── test_health.py       # Health endpoint tests
├── .github/
│   └── workflows/
│       └── backend-ci.yml   # CI/CD pipeline (lint, test, build)
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # PostgreSQL + API services
├── pyproject.toml           # Poetry dependencies
├── .env.example             # Environment template
├── .gitignore
├── .dockerignore
└── README.md
```

## Local Development

### Prerequisites

- Python 3.12+
- Poetry
- PostgreSQL 16
- Docker & Docker Compose (optional)

### Setup

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Start PostgreSQL (via docker-compose):**
   ```bash
   docker-compose up -d postgres
   ```

4. **Run application:**
   ```bash
   poetry run uvicorn app.main:app --reload --port 9180
   ```

5. **Access API:**
   - Health check: http://localhost:9180/health
   - API docs: http://localhost:9180/docs

## Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f ledger-api

# Stop services
docker-compose down
```

## Testing

Tests use PostgreSQL (SQLite is forbidden). A test database is required.

```bash
# Start test database
docker-compose up -d postgres

# Run all tests
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test
poetry run pytest tests/test_health.py -v
```

## Linting

```bash
# Check code style
poetry run ruff check .

# Auto-fix issues
poetry run ruff check . --fix
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+pg8000://ledger:ledger@localhost:5432/nex_ledger` | PostgreSQL connection string (pg8000 driver) |
| `PORT` | `9180` | Application port |
| `ENV` | `development` | Environment (development/production) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## Health Check

```bash
curl http://localhost:9180/health
# {"status": "ok", "service": "nex-ledger"}
```

## Tech Stack

- **Backend:** FastAPI 0.109+
- **Database:** PostgreSQL 16 (pg8000 driver)
- **Python:** 3.12+
- **ORM:** SQLAlchemy 2.0
- **Testing:** pytest, httpx
- **Linting:** ruff
- **Container:** Docker (python:3.12-slim)
