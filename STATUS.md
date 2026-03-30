# NEX-Ledger — Current Status
Last updated: 2026-03-30

## Current State
- **Phase:** Early development — domain model layer complete, schema layer complete, service layer growing
- **Models defined:** 14 (Currency, AccountType, TaxRate, BusinessPartner, ChartOfAccounts, ImportBatch, AccountingPeriod, Account, JournalEntry, JournalEntryLine, OpeningBalance, SourceDocument, DocumentEntryLink)
- **Schemas:** 17 — `PaginatedResponse[T]`, Currency (C/R/U), AccountType (C/R/U), TaxRate (C/R/U), BusinessPartner (C/R/U), ChartOfAccounts (C/R/U), ImportBatch (C/R/U), AccountingPeriod (C/R/U), Account (C/R/U), JournalEntryLine (C/R/U), JournalEntry (C/R/U), OpeningBalance (C/R/U), SourceDocument (C/R/U)
- **Services:** 10 — `CurrencyService` (5 methods, natural key CRUD), `AccountTypeService` (5 methods, normal_balance validation, FK guard), `TaxRateService` (5 methods, name+rate validation, FK guard), `BusinessPartnerService` (5 methods, name validation, FK guard), `ChartOfAccountsService` (5 methods, name+code validation, FK guard), `AccountingPeriodService` (5 methods, temporal validation, overlap detection), `AccountService` (5 methods + circular ref detection), `JournalEntryService` (10 methods), `ImportService`, `SourceDocumentService` (5 methods, FK guard via DocumentEntryLink)
- **Migrations:** 14 sequential Alembic migrations (001–014)
- **Tests:** 370 passing
- **API:** Only `GET /health` endpoint implemented
- **CI:** `ubuntu-latest` pipeline — lint ✅, test ✅, docker-build ✅
- **CD:** Tag-triggered placeholder workflow (`cd.yml`) ready for deploy integration
- **Deployed:** Docker Compose (app on port 9180, PostgreSQL 16 on port 9181)

## Recent Changes
- **2026-03-30** — Added SourceDocumentService with full CRUD: `list_documents` (paginated, ordered by document_id ASC), `get_document`, `create_document` (document_number + document_type validation), `update_document`, `delete_document` (FK guard via DocumentEntryLink), 13 new tests in 5 classes — CI all green (370 total)
- **2026-03-30** — Added AccountingPeriodService with full CRUD: `list_periods` (paginated, ordered by start_date DESC), `get_period`, `create_period` (temporal validation start<end, overlap detection per chart_id), `update_period` (revalidation, self-exclude overlap), `delete_period` (FK guard via opening_balance.period_id), 15 new tests in 5 classes — CI all green (343 total)
- **2026-03-30** — Added ChartOfAccountsService with full CRUD: `list_charts` (paginated, ordered by chart_id), `get_chart`, `create_chart` (name+code validation), `update_chart`, `delete_chart` (FK guard via account table), 13 new tests in 5 classes — CI all green (328 total)
- **2026-03-30** — Added BusinessPartnerService with full CRUD: `list_partners` (paginated, ordered by partner_id), `get_partner`, `create_partner` (name validation), `update_partner`, `delete_partner` (FK guard via JournalEntryLine.partner_id), 14 new tests in 5 classes — CI all green (315 total)
- **2026-03-30** — Added TaxRateService with full CRUD: `list_tax_rates` (paginated), `get_tax_rate`, `create_tax_rate` (name+rate validation), `update_tax_rate`, `delete_tax_rate` (FK guard via JournalEntryLine), 13 new tests in 5 classes — CI all green (301 total)
- **2026-03-30** — Added AccountTypeService with full CRUD: `list_account_types` (paginated), `get_account_type`, `create_account_type` (name + normal_balance validation), `update_account_type`, `delete_account_type` (FK guard via account table), 14 new tests — CI all green (288 total)
- **2026-03-30** — Added CurrencyService with natural key CRUD: `list_currencies` (paginated), `get_currency` (by code), `create_currency` (3-char uppercase validation, duplicate check), `update_currency` (immutable PK), `delete_currency` (FK guard via journal_entry_line), 18 new tests — CI all green (274 total)
- **2026-03-30** — Extended AccountService with full CRUD: `list_accounts` (paginated, ordered by account_number), `get_account`, `create_account` (parent validation), `update_account` (circular reference detection), `delete_account` (child/balance guards), 17 new tests — CI all green (256 total)
- **2026-03-30** — Extended JournalEntryService with full CRUD: 5 entry methods + 5 line methods, double-entry revalidation on every line mutation, 17 tests — CI all green
- **2026-03-30** — Added ImportService CRUD: batch creation, status management tests
- **2026-03-30** — Added DocumentEntryLink Pydantic schemas
- **2026-03-30** — Added SourceDocument Pydantic schemas: document_type Literal enum, partner_id gt=0, total_amount ≥0 2dp, 9 unit tests — CI all green
- **2026-03-30** — Added OpeningBalance Pydantic schemas
- **2026-03-30** — Added JournalEntry + JournalEntryLine Pydantic schemas: nested lines (min 1), 11 unit tests — CI all green
- **2026-03-30** — Added Account Pydantic schemas: FK validations, level 0–10, Decimal balances 2dp, 10 unit tests — CI all green
- **2026-03-30** — Added AccountingPeriod, ImportBatch, ChartOfAccounts, BusinessPartner, TaxRate, AccountType, Currency schemas + unit tests
- **2026-03-30** — Created `app/schemas/` package with `PaginatedResponse[T]` generic class, `tests/unit/` directory

## Known Issues
- No REST API endpoints beyond `/health` — models exist but no CRUD operations
- No authentication/authorization layer yet
- No frontend
- CD workflow (`cd.yml`) is a placeholder — deploy step not yet implemented

## Next Steps
- Service layer complete (all 10 services implemented)
- Implement CRUD API endpoints (routers) for existing services
- Add authentication layer
- Add reporting/query endpoints using AccountService statement generation
- Integrate ANDROS deploy agent into `cd.yml` for automated tag-triggered deployments
