# NEX-Ledger — Architecture
Last updated: 2026-03-30

## Tech Stack
| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web Framework | FastAPI 0.115.14 |
| ASGI Server | Uvicorn 0.30.6 |
| ORM | SQLAlchemy 2.0.48 (synchronous) |
| Database | PostgreSQL 16 (Alpine) |
| DB Driver | pg8000 1.31.5 |
| Migrations | Alembic 1.18.4 |
| Validation | Pydantic 2.12.5 + Pydantic Settings 2.13.1 |
| Testing | pytest 8.0.0, pytest-cov, httpx 0.27.0, Codecov |
| Linting | Ruff 0.5.0 |
| Deps | Poetry 1.7.1 |
| Prod ASGI Server | Gunicorn 25.3.0 + Uvicorn workers |
| Containers | Docker multi-stage, Docker Compose |

## Components
| Component | Technology | Purpose |
|---|---|---|
| `app/main.py` | FastAPI | App entry point, health endpoint (port 9180) |
| `app/config.py` | Pydantic Settings | Environment-based configuration |
| `app/database.py` | SQLAlchemy | Sync engine & session factory |
| `app/models/base.py` | SQLAlchemy | UUIDMixin, TimestampMixin base classes |
| `app/models/` | SQLAlchemy | 14 domain models (Currency → DocumentEntryLink) |
| `app/schemas/common.py` | Pydantic V2 | `PaginatedResponse[T]` generic paginated response |
| `app/schemas/currency.py` | Pydantic V2 | `CurrencyCreate`, `CurrencyRead`, `CurrencyUpdate` — ISO 4217 validation, ORM mode |
| `app/schemas/account_type.py` | Pydantic V2 | `AccountTypeCreate`, `AccountTypeRead`, `AccountTypeUpdate` — code/name constraints, ORM mode |
| `app/schemas/tax_rate.py` | Pydantic V2 | `TaxRateCreate`, `TaxRateRead`, `TaxRateUpdate` — Decimal rate (0–100, 4dp), date ranges |
| `app/schemas/business_partner.py` | Pydantic V2 | `BusinessPartnerCreate`, `BusinessPartnerRead`, `BusinessPartnerUpdate` — Literal type, email validator |
| `app/schemas/chart_of_accounts.py` | Pydantic V2 | `ChartOfAccountsCreate`, `ChartOfAccountsRead`, `ChartOfAccountsUpdate` — code/name constraints, ORM mode |
| `app/services/` | Python | Business logic layer (10 services) |
| `app/services/currency_service.py` | Python | Natural key CRUD (5 methods), 3-char code validation, FK guard on delete |
| `app/services/account_type_service.py` | Python | Full CRUD (5 methods), normal_balance validation (debit/credit), FK guard via account table |
| `app/services/tax_rate_service.py` | Python | Full CRUD (5 methods), name+rate validation, FK guard via JournalEntryLine |
| `app/services/business_partner_service.py` | Python | Full CRUD (5 methods), name validation, FK guard via JournalEntryLine.partner_id |
| `app/services/chart_of_accounts_service.py` | Python | Full CRUD (5 methods), name+code validation, FK guard via account table |
| `app/services/accounting_period_service.py` | Python | Full CRUD (5 methods), temporal validation (start<end), overlap detection per chart_id, FK guard via opening_balance |
| `app/services/account_service.py` | Python | Full CRUD (list/get/create/update/delete), circular reference detection, balance reconciliation, account statements |
| `app/services/journal_entry_service.py` | Python | Double-entry validation, balance calculation (10 methods) |
| `app/services/import_service.py` | Python | Batch creation, status management |
| `app/services/source_document_service.py` | Python | Full CRUD (5 methods), document_number+type validation, FK guard via DocumentEntryLink |
| `alembic/` | Alembic | 14 sequential migrations |
| `tests/` | pytest | Integration tests (model tests, service tests, health endpoint) |
| `tests/unit/` | pytest | Unit tests (schema tests — all 17 schema sets) |
| `tests/services/` | pytest | Service CRUD tests (CurrencyService, AccountTypeService, TaxRateService, BusinessPartnerService, ChartOfAccountsService, AccountingPeriodService, AccountService, JournalEntryService, ImportService, SourceDocumentService) |
| `Dockerfile.prod` | Docker | Multi-stage production build (builder → runtime, 186MB) |
| `docker-compose.prod.yml` | Docker Compose | Production stack (GHCR image, named volumes, env secrets) |
| `docker/init-db.sh` | Bash | Creates test database on startup |
| `.github/workflows/ci.yml` | GitHub Actions | lint → test → docker-build pipeline (ubuntu-latest) |
| `.github/workflows/cd.yml` | GitHub Actions | Tag-triggered deploy placeholder (`v*` tags) |
| `.github/workflows/deploy.yml` | GitHub Actions | Manual deploy via docker compose (workflow_dispatch) |

## Data Flow
1. Client → FastAPI (port 9180) → Pydantic schemas (validation) → Service layer → SQLAlchemy sync session → PostgreSQL 16
2. Request schemas (`*Create`, `*Update`) validate input; Response schemas (`*Read`, `PaginatedResponse[T]`) serialize output with ORM mode
3. Service layer: `CurrencyService` natural key CRUD; `AccountTypeService` CRUD + normal_balance validation; `TaxRateService` CRUD + rate validation; `BusinessPartnerService` CRUD + name validation; `ChartOfAccountsService` CRUD + name+code validation; `AccountingPeriodService` CRUD + temporal validation + overlap detection; `AccountService` full CRUD + balance reconciliation + circular reference detection; `JournalEntryService` full CRUD + double-entry validation; `ImportService` batch creation + status management; `SourceDocumentService` full CRUD + FK guard via DocumentEntryLink
3. Alembic manages schema migrations in numbered sequence (001–014)
4. Tests use transactional fixtures with auto-rollback per test function

## Infrastructure
- **Production app:** `Dockerfile.prod` — multi-stage (builder: Poetry export → pip wheel; runtime: Python 3.12-slim, 186MB), Gunicorn 4× Uvicorn workers, non-root `nexledger:1000`, healthcheck via `urllib.request`
- **Production compose:** `docker-compose.prod.yml` — image from `ghcr.io/rauschiccsk/nexledger:latest`, `restart: always`, no volume mounts on app (stateless), named volume `nexledger-db-data`, env-based secrets
- **Dev app container:** `nexledger-app` — Python 3.12-slim, non-root user `nexledger:1000`
- **DB container:** `nexledger-db` — PostgreSQL 16-alpine, healthcheck via `pg_isready`
- **Network:** `nexledger-network` (Docker bridge)
- **Ports:** 9180 (app), 9181 (PostgreSQL external)
- **CI runner:** `ubuntu-latest` (GitHub-hosted) with PostgreSQL 16-alpine service container
- **CD trigger:** Push tags matching `v*` (placeholder — deploy step TBD)
- **Legacy deploy:** `deploy.yml` on self-hosted `[self-hosted, andros]` via `workflow_dispatch`

## Key Decisions
- **Synchronous SQLAlchemy** — pg8000 driver per ICC standard, no async complexity
- **Integer PKs** — Most models use auto-increment Integer PK (not UUID)
- **Server-side defaults** — `func.now()`, `func.clock_timestamp()`, `uuid_generate_v4()` for DB-level consistency
- **Soft deletes** — `is_active` boolean pattern for history preservation
- **PostgreSQL-specific features** — JSONB (ImportBatch.validation_report), UUID extension, timezone-aware timestamps
- **ICC Port Registry** — Standardized port 9180 for all NEX services
- **Sequential migrations** — Numbered 001–014 with explicit `down_revision` chain
- **Self-FK via ALTER TABLE** — Account.parent_account_id added post-CREATE to avoid circular reference in DDL
- **DB-level triggers** — `update_account_updated_at()` trigger for automatic timestamp updates on Account
- **Named constraints** — Explicit constraint names (e.g. `uq_journal_entry_entry_number`, `fk_jel_*`, `fk_ob_*`) for predictable migration management
- **TIMESTAMP WITH TIME ZONE** — JournalEntry uses timezone-aware timestamps for correct multi-timezone handling
- **CASCADE on composition relationships** — OpeningBalance deleted when parent AccountingPeriod or Account is deleted (composition semantics)
- **RESTRICT on reference relationships** — SourceDocument prevents deletion of referenced BusinessPartner or Currency (referential integrity)
- **Decimal precision via Numeric(15,2)** — Account balances use PostgreSQL Numeric mapped to Python Decimal, avoiding floating-point errors
- **CI on ubuntu-latest** — GitHub-hosted runners for CI (lint, test, docker-build); self-hosted reserved for production deploy
- **CI test DB as service container** — PostgreSQL 16-alpine runs as GitHub Actions service, matching production DB version
- **Gunicorn in production** — 4 Uvicorn workers via Gunicorn for process management, graceful restarts, and multi-core utilization
- **Multi-stage Docker build** — Builder stage (Poetry export + pip wheel) separated from runtime (no compiler, no Poetry, no curl) for minimal attack surface and 186MB image
- **Stateless app container** — No volume mounts on production app; all state in PostgreSQL with named volume persistence
- **Three-schema pattern (Create/Read/Update)** — Separate Pydantic models per entity for input validation, ORM serialization, and partial updates; keeps API contract explicit and type-safe
- **Service layer uses flush, never commit** — All services call `session.flush()` for DB writes, leaving transaction control to the caller (UoW pattern)
- **ValueError for business errors** — Services raise `ValueError` with descriptive messages for not-found, constraint violations, and circular references
