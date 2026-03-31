# NEX Ledger — Architectural Design Document v0.8

## CHANGELOG

| Verzia | Dátum      | Zmeny |
|--------|------------|-------|
| v0.8   | 2026-03-29 | Section 6 (REST API Architecture) + Section 7 (Frontend Architecture): CRUD endpointy, Pydantic schémy, špeciálne endpointy, service layer extension, React frontend s routing a komponentmi. Prečíslovanie sekcií 6-13 → 8-15. |
| v0.7   | 2026-03-29 | Service layer documentation: JournalEntryService, ImportService, AccountService methods + conventions. |
| v0.6   | 2026-03-29 | Phase 3 implementation sync: deferred column annotations for JournalEntryLine, OpeningBalance, SourceDocument, DocumentEntryLink. FK ON DELETE typy explicitne uvedené. |
| v0.5   | 2026-03-28 | Phase 2 implementation sync: deferred column annotations for AccountingPeriod, Account, JournalEntry. FK ON DELETE typy explicitne uvedené. |
| v0.4   | 2026-03-28 | Doplnenie lookup tabuliek do Section 5: currency, account_type, tax_rate. Rozšírenie business_partner o partner_type, code, kontaktné údaje. Upresenie chart_of_accounts ako framework entity. Synchronizácia s Phase 1 implementáciou. |
| v0.3   | 2026-03-24 | Oprava port assignment: 9170/9171 → 9180/9181 (9170/9171 obsadené NEX Marketing). Otvorená otázka #2 (NEX Marketing port reassignment) odstránená — Marketing si ponecháva 9170/9171. |
| v0.2   | 2026-03-21 | Oprava číslovaní sekcií 4.x (chýbajúci header 4.4 Ledger Core, duplikáty 4.4/4.5), oprava duplikátu sekcie 9, doplnenie `opening_balance` entity do DB schémy, prečíslovanie sekcií 9–12 |
| v0.1   | 2026-03-19 | Iniciálny architektonický návrh |

## 1. VÍZIA

NEX Ledger je plne automatizovaný účtovný systém pre podvojné účtovníctvo slovenských s.r.o., ktorý pokrýva celý lifecycle od importu denníka až po elektronické podanie na portál Finančnej správy.

**Kľúčový princíp:** Zero-touch year-end — kompletná účtovná uzávierka jedným kliknutím.

## 2. SCOPE

| Oblasť | Pokrytie |
|---------|----------|
| Hlavná kniha | Vlastný full ledger, immutable journal (append-only) |
| Účtovná závierka | Súvaha, Výkaz ziskov a strát, Poznámky — plný výpočet (nahrádza externú účtovníčku) |
| Daň z príjmov PO | Plný výpočet základu dane + generovanie DP PO XML (nahrádza externú účtovníčku) |
| DPH | XML generovanie z NEX Genesis dát + podanie na FS (nahrádza program eDane) |
| Podanie na FS | Priama API integrácia (eID/KEP) — DPH výkazy + DP PO + účtovná závierka |
| Multi-tenant | Schema-per-tenant (ICC štandard), 7+ firiem |
| Vstup | Excel (XLS/XLSX) denník + CSV/TXT knihy OF, DF, pokladňa z NEX Genesis |
| Štartové obdobie | Účtovný rok 2025 |

## 3. ARCHITEKTÚRA

### 3.1 Tech Stack

- Backend: FastAPI (Python 3.12+)
- Database: PostgreSQL 16 (schema-per-tenant)
- Config: pydantic-settings (env_file + environment variables)
- AI Layer: Ollama (lokálny LLM na ANDROS)
- Containerizácia: Docker + Docker Compose
- Server: ANDROS (100.107.134.104)
- CI/CD: GitHub Actions (self-hosted runner)

### 3.2 Port Assignment (ICC Port Registry)

| Služba | Port |
|--------|------|
| NEX Ledger API (backend) | 9180 |
| NEX Ledger PostgreSQL | 9181 |
| NEX Ledger Frontend | 9182 |

### 3.3 Repository

- GitHub: `rauschiccsk/nex-ledger`
- Doména: `ledger.isnex.eu`

### 3.4 High-Level Architecture

```
            REST API clients
                 |
                 v
     NEX Ledger API (:9180)
     FastAPI (API-only, no frontend)
+------------+ +------------+ +------------+ +--------------+
|  Import    | |  Ledger    | |  Reports   | |  FS Portal   |
|  Engine    | |  Core      | |  Engine    | |  Connector   |
+------------+ +------------+ +------------+ +--------------+
+------------+ +------------+ +------------+
|   Tax      | |    AI      | |  Audit     |
|  Engine    | | Validator  | |  Trail     |
+------------+ +------------+ +------------+
        |
   -----+-----+-------------+
   v          v              v
PostgreSQL  Ollama       FS Portal
 (:9181)    (:9132)        API
```

## 4. CORE MODULES

### 4.1 Import Engine

Účel: Parsovanie vstupných dát z NEX Genesis, validácia, transformácia do interného formátu.

Dva vstupné kanály:

**A) Účtovný denník (Excel XLS/XLSX):**
- Parsovanie cez openpyxl/xlrd
- Mapovanie stĺpcov (konfigurovateľné per tenant)
- Validácia: MD=D kontrola, existencia účtov, dátumové rozsahy
- Duplikačná ochrana (hash-based detection)
- Výstup: importované záznamy v hlavnej knihe

**B) Prvotné doklady (CSV/TXT):**
- Kniha odberateľských faktúr (OF)
- Kniha dodávateľských faktúr (DF)
- Pokladničné doklady
- Parsovanie cez Papaparse (auto-detect delimiter, encoding cp852/utf-8)
- Validácia: povinné polia (partner, suma, DPH, dátum, VS, číslo dokladu)
- Duplikačná ochrana (číslo dokladu + tenant = unique)
- Výstup: importované doklady v source_document tabuľke

**Import workflow:**
1. Import prvotných dokladov (OF, DF, pokladňa)
2. Import účtovného denníka
3. Automatické prelinkovanie: journal_entry ↔ source_document (podľa čísla dokladu / VS)
4. Three-Way Reconciliation check (okamžitý)

### 4.2 Source Documents (Prvotné doklady)

Účel: Evidencia prvotných dokladov ako základ pre krížové kontroly.

Kľúčové entity:

```
source_document
├── document_id (PK, SERIAL) [IMPLEMENTED Phase 3] — Integer PK; UUID migrácia [DEFERRED]
├── document_type (VARCHAR(50), NOT NULL — issued_invoice | received_invoice | cash_receipt) [IMPLEMENTED Phase 3]
├── document_number (VARCHAR(50), NOT NULL, UNIQUE) [IMPLEMENTED Phase 3]
├── issue_date (DATE, NOT NULL — dátum vystavenia) [IMPLEMENTED Phase 3]
├── partner_id (INTEGER, NOT NULL, FK → business_partner, ON DELETE RESTRICT) [IMPLEMENTED Phase 3]
├── total_amount (NUMERIC(15,2), NOT NULL) [IMPLEMENTED Phase 3]
├── currency_code (VARCHAR(3), NOT NULL, FK → currency, ON DELETE RESTRICT) [IMPLEMENTED Phase 3] — nahradil denormalizovaný currency string
├── created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, server_default now()) [IMPLEMENTED Phase 3]
├── variable_symbol [DEFERRED Phase 4+] — variabilný symbol pre párovanie platieb
├── delivery_date (DATE — dátum dodania / plnenia) [DEFERRED Phase 4+] — DPH plnenie
├── due_date (DATE — dátum splatnosti) [DEFERRED Phase 4+] — splatnosť faktúry
├── tax_base (NUMERIC(15,2)) [DEFERRED Phase 4+] — základ dane
├── vat_amount (NUMERIC(15,2)) [DEFERRED Phase 4+] — suma DPH
├── vat_rate (NUMERIC(5,2)) [DEFERRED Phase 4+] — sadzba DPH
├── payment_status (unpaid | partial | paid) [DEFERRED Phase 4+] — stav úhrady
├── import_batch_id (FK → import_batch) [DEFERRED Phase 4+] — väzba na import batch
└── document_hash (SHA-256) [DEFERRED Phase 5+] — integrita dokladu
UNIQUE: (document_number) — uq_document_number
```

```
document_entry_link
├── link_id (PK, SERIAL) [IMPLEMENTED Phase 3]
├── document_id (INTEGER, NOT NULL, FK → source_document, ON DELETE CASCADE) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: source_document_id)
├── entry_id (INTEGER, NOT NULL, FK → journal_entry, ON DELETE CASCADE) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: journal_entry_id)
├── created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, server_default now()) [IMPLEMENTED Phase 3]
├── link_type (auto | manual) [DEFERRED Phase 4+] — typ prelinkovania
├── link_confidence (NUMERIC(5,2) — pre AI matching) [DEFERRED Phase 5+] — AI matching confidence score
└── linked_at [DEFERRED Phase 4+] — nahradené created_at v Phase 3
UNIQUE: (document_id, entry_id) — uq_document_entry
```

**Linking strategy (3 úrovne):**
1. Deterministický: document_number = source_document_ref v journal_entry → 100% match
2. Heuristický: VS + suma + dátum ± 3 dni → vysoká pravdepodobnosť
3. AI matching (Ollama): Fuzzy matching pre zostávajúce neprelinované záznamy

### 4.3 Three-Way Reconciliation Engine

Účel: Kontinuálna krížová kontrola medzi prvotným dokladom, účtovným zápisom a výkazom. Toto je kľúčová inovatívna funkcia — manuálne nerealizovateľné, AI robí pri každom importe.

**Kontrolná matica:**

| # | Kontrola | Zdroj A | Zdroj B | Typ |
|---|----------|---------|---------|-----|
| R1 | Kompletnosť OF | Kniha OF | Journal entries (311/6xx) | Doklad → Zápis |
| R2 | Kompletnosť DF | Kniha DF | Journal entries (321/5xx, 321/0xx) | Doklad → Zápis |
| R3 | Kompletnosť pokladne | Pokladničné doklady | Journal entries (211/xxx) | Doklad → Zápis |
| R4 | Oprávnenosť zápisov | Journal entries | Source documents | Zápis → Doklad |
| R5 | Sumárna OF | SUM(OF.total_amount) | Obrat účtu 311 | Sumárna |
| R6 | Sumárna DF | SUM(DF.total_amount) | Obrat účtu 321 | Sumárna |
| R7 | Sumárna pokladňa | SUM(príjmy) / SUM(výdavky) | Obrat MD/D účtu 211 | Sumárna |
| R8 | DPH OF | SUM(OF.vat_amount) | Obrat D účtu 343 (výstupná) | DPH |
| R9 | DPH DF | SUM(DF.vat_amount) | Obrat MD účtu 343 (vstupná) | DPH |
| R10 | KV vs knihy | Kontrolný výkaz | Kniha OF + DF | DPH |

**Výstup per kontrola:**
- PASS — zhoda (tolerancia ±0.01 € na zaokrúhlenie)
- WARN — malý rozdiel (do 1 €) — pravdepodobne zaokrúhlenie
- FAIL — významný rozdiel — vyžaduje investigation

**Integrácia s Continuous Closing:** Three-Way Reconciliation je súčasťou mesačného Continuous Closing cyklu. Readiness Score zohľadňuje výsledky — ak je FAIL, score klesá.

**Integrácia s Accounting DNA:** S prvotným dokladom má AI bohatší kontext pre Confidence Score: dodávateľ, položky, sumy — nie len číslo účtu a celková suma.

### 4.4 Ledger Core (Hlavná kniha)

Účel: Srdce systému — immutable double-entry ledger.

**Princípy:**
- Immutable Journal: Každý zápis je nemenný (append-only). Opravy len cez stornovací zápis (§34 zákona č. 431/2002 Z.z.)
- Double-entry enforcement: Každá transakcia MUSÍ mať MD=D, databázový constraint
- Účtový rozvrh: Konfigurovateľný per tenant, predvolená šablóna podľa Opatrenia MF SR
- Obdobia: Účtovné obdobia s lock mechanizmom (uzavreté obdobie = read-only)

**Kľúčové entity:**
- `accounting_period` — účtovné obdobie (rok), stav (open/closing/closed)
- `chart_of_accounts` — účtový rozvrh (syntetické + analytické účty)
- `journal_entry` — účtovný zápis (hlavička)
- `journal_entry_line` — riadky zápisu (účet, MD/D, suma)
- `opening_balance` — počiatočné stavy účtov

### 4.5 Reports Engine (Účtovné výkazy)

Účel: Automatické generovanie všetkých zákonných výkazov.

**Výkazy:**
1. Súvaha (Balance Sheet) — Opatrenie MF SR č. 4455/2003-92, vzor Úč ROPO SFOV 1-01
2. Výkaz ziskov a strát (P&L) — druhové členenie pre s.r.o.
3. Poznámky k účtovnej závierke — šablóna s automatickým vyplnením číselných údajov

**Mapovanie:** Každý riadok výkazu je definovaný ako formula nad účtami (napr. riadok 001 Súvahy = SUM(011xx) - SUM(07xxx)). Tieto mapovania sú konfigurovateľné a verzionované (legislatíva sa mení).

**Výstupy:** PDF, XLSX, XML (pre FS portál)

### 4.6 Tax Engine (Daňové výpočty)

Účel: Generovanie XML výkazov a výpočet daňových povinností.

**Moduly:**

**1. DPH Priznanie — XML generovanie (nie výpočet)**
- Vstup: DPH dáta z NEX Genesis (importované cez Import Engine)
- NEX Genesis počíta DPH spoľahlivo desaťročia — NEX Ledger NEPOČÍTA DPH
- NEX Ledger transformuje importované dáta do XML podľa XSD schémy FS
- XSD validácia pred odoslaním
- Nahrádza program eDane (klient FS)

**2. Kontrolný výkaz DPH — XML generovanie**
- Vstup: faktúry z NEX Genesis s DPH príznakom
- Automatické zostavenie častí A.1, A.2, B.1, B.2, B.3, C.1, C.2, D.1, D.2
- XML generovanie + XSD validácia

**3. Súhrnný výkaz DPH — XML generovanie**
- Vstup: intrakomunitárne dodania z NEX Genesis
- XML generovanie + XSD validácia

**4. DP PO (Daňové priznanie k dani z príjmov PO) — plný výpočet**
- Toto je HLAVNÁ úloha, ktorú dnes robí externá účtovníčka
- Výpočet základu dane z účtovného výsledku hospodárenia
- Pripočítateľné a odpočítateľné položky (§ 17–29 zákona 595/2003)
- Sadzba dane (21% / 15% pre malé podniky s obratom do 60 000 €)
- Daňová licencia (ak je relevantná)
- Generovanie XML podľa schémy FS

**Kľúčové rozlíšenie:**
- DPH = NEX Genesis počíta, NEX Ledger len generuje XML a podáva (nahrádza eDane)
- DP PO = NEX Ledger plne počíta a generuje (nahrádza externú účtovníčku)

### 4.7 FS Portal Connector

Účel: Priama elektronická komunikácia s portálom Finančnej správy.

**Fázy implementácie:**
1. Fáza 1 (MVP): Generovanie XML súborov v správnom formáte (validácia XSD)
2. Fáza 2: Automatický upload cez API portálu FS
3. Fáza 3: eID/KEP podpisovanie a plná automatizácia

**Technické aspekty:**
- XML schémy FS (verejne dostupné na financnasprava.sk)
- Kvalifikovaný elektronický podpis (KEP) — integrácia s D.Suite/eID klient
- SOAP/REST API portálu (ak je dostupné) alebo automatizácia cez Playwright

**Bezpečnosť:**
- Podpisové certifikáty: uložené vo Vaultwarden alebo HSM
- Audit log: každé podanie zaznamenané s timestamp + hash

### 4.8 AI Validation Layer

Účel: Inteligentná kontrola kvality účtovných dát.

**Funkcionalita:**
1. Pre-import validácia: Kontrola konzistencie Excel dát pred importom
2. Anomaly detection: Nezvyčajné sumy, neštandardné účtovné predpisy, duplicity
3. Cross-period consistency: Porovnanie s predchádzajúcimi obdobiami
4. Completeness check: Kontrola, či sú všetky povinné účtovné operácie zaúčtované (odpisy, kurzové rozdiely, časové rozlíšenie, daňové rezervy)
5. Pre-submission review: Finálna kontrola pred podaním na FS

Technológia: Ollama (lokálny LLM na ANDROS) — žiadne dáta neopúšťajú infraštruktúru.

### 4.9 Audit Trail

Účel: Kompletná sledovateľnosť všetkých operácií.

- Kto, kedy, čo — každá akcia zaznamenaná
- Immutable log (append-only, rovnaký princíp ako journal)
- Podpora pre audit / daňovú kontrolu
- Export audit trail pre externého audítora

## 5. DATABASE DESIGN (Core Entities)

Schema: `ledger_{tenant_id}`

```
currency
├── currency_code (PK, VARCHAR(3), ISO 4217 — napr. EUR, USD, CZK)
├── name (VARCHAR(100), NOT NULL)
├── symbol (VARCHAR(10), nullable — napr. €, $, Kč)
├── decimal_places (SMALLINT, NOT NULL, server_default 2)
├── is_active (BOOLEAN, NOT NULL, server_default TRUE)
└── updated_at (TIMESTAMP WITH TIME ZONE, server_default now(), onupdate clock_timestamp())

account_type
├── account_type_id (PK, SERIAL)
├── code (VARCHAR(20), UNIQUE — napr. ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE)
├── name (VARCHAR(100), NOT NULL)
└── description (TEXT, nullable)

tax_rate
├── tax_rate_id (PK, SERIAL)
├── code (VARCHAR(20), UNIQUE — napr. VAT20, VAT10)
├── name (VARCHAR(100), NOT NULL)
├── rate (NUMERIC(5,2), NOT NULL, CHECK 0-100)
├── valid_from (DATE, nullable)
├── valid_to (DATE, nullable)
└── is_active (BOOLEAN, NOT NULL, server_default TRUE)

accounting_period
├── period_id (PK, SERIAL) [IMPLEMENTED Phase 2]
├── chart_id (INTEGER, NOT NULL, FK → chart_of_accounts, ON DELETE CASCADE) [IMPLEMENTED Phase 2]
├── year (INTEGER, NOT NULL — 2025, 2026, ...) [IMPLEMENTED Phase 2]
├── period_number (SMALLINT, NOT NULL — 1-12 alebo 13 pre uzávierku) [IMPLEMENTED Phase 2]
├── start_date (DATE, NOT NULL) [IMPLEMENTED Phase 2]
├── end_date (DATE, NOT NULL) [IMPLEMENTED Phase 2]
├── is_closed (BOOLEAN, NOT NULL, server_default FALSE) [IMPLEMENTED Phase 2]
├── status (open | closing | closed) [DEFERRED Phase 4+] — nahradené is_closed boolean v Phase 2
├── opened_at, closed_at [DEFERRED Phase 4+] — audit trail timestamps
└── closed_by [DEFERRED Phase 4+] — audit trail user reference
UNIQUE: (chart_id, year, period_number) — uq_chart_year_period

chart_of_accounts  (= účtová osnova/framework, NIE individuálne účty)
├── chart_id (PK, SERIAL)
├── code (VARCHAR(20), UNIQUE — napr. 'SK-UCTO-2024')
├── name (VARCHAR(100), NOT NULL)
└── description (TEXT, nullable)
Poznámka: Toto je kontajner pre účtový rozvrh. Individuálne účty (account_number,
account_type_id, currency_code, parent) sú v tabuľke `account` (FK → chart_of_accounts).

account (= individuálne účty v rámci účtového rozvrhu)
├── account_id (PK, SERIAL) [IMPLEMENTED Phase 2]
├── chart_id (INTEGER, NOT NULL, FK → chart_of_accounts, ON DELETE CASCADE) [IMPLEMENTED Phase 2]
├── account_number (VARCHAR(20), NOT NULL — napr. '343000') [IMPLEMENTED Phase 2]
├── name (VARCHAR(200), NOT NULL — napr. 'Daň z pridanej hodnoty') [IMPLEMENTED Phase 2]
├── account_type_id (INTEGER, NOT NULL, FK → account_type, ON DELETE RESTRICT) [IMPLEMENTED Phase 2]
├── currency_code (VARCHAR(3), NOT NULL, FK → currency, ON DELETE RESTRICT) [IMPLEMENTED Phase 2]
├── parent_account_id (INTEGER, nullable, FK → self, ON DELETE SET NULL — pre analytiku) [IMPLEMENTED Phase 2]
├── level (SMALLINT, NOT NULL — hierarchy depth: 1=root, 2=child, ...) [IMPLEMENTED Phase 2]
├── is_active (BOOLEAN, NOT NULL, server_default TRUE) [IMPLEMENTED Phase 2]
├── opening_balance (NUMERIC(15,2), server_default 0) [IMPLEMENTED Phase 2]
├── current_balance (NUMERIC(15,2), server_default 0) [IMPLEMENTED Phase 2]
├── updated_at (TIMESTAMP WITH TIME ZONE, NOT NULL, server_default now(), onupdate now()) [IMPLEMENTED Phase 2]
├── account_class (0-9, trieda účtov) [DEFERRED Phase 4+] — Slovak accounting classification
└── valid_from, valid_to [DEFERRED Phase 4+] — temporal validity of account
UNIQUE: (chart_id, account_number) — uq_chart_account_number

opening_balance
├── balance_id (PK, SERIAL) [IMPLEMENTED Phase 3]
├── period_id (INTEGER, NOT NULL, FK → accounting_period, ON DELETE CASCADE) [IMPLEMENTED Phase 3]
├── account_id (INTEGER, NOT NULL, FK → account, ON DELETE CASCADE) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: FK → chart_of_accounts — opravené na account)
├── debit_amount (NUMERIC(15,2), server_default 0) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: debit_balance)
├── credit_amount (NUMERIC(15,2), server_default 0) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: credit_balance)
├── created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, server_default now()) [IMPLEMENTED Phase 3]
├── source (import | carry_forward | manual) [DEFERRED Phase 4+] — zdroj počiatočného stavu
├── import_batch_id (FK → import_batch, nullable) [DEFERRED Phase 4+] — väzba na import batch
├── created_by [DEFERRED Phase 4+] — audit trail user reference
└── note (TEXT, nullable) [DEFERRED Phase 4+] — poznámka k počiatočnému stavu
UNIQUE: (period_id, account_id) — uq_period_account

journal_entry
├── entry_id (PK, SERIAL) [IMPLEMENTED Phase 2] — Integer PK; UUID migrácia [DEFERRED]
├── batch_id (INTEGER, nullable, FK → import_batch, ON DELETE SET NULL) [IMPLEMENTED Phase 2]
├── entry_number (VARCHAR(50), NOT NULL, UNIQUE) [IMPLEMENTED Phase 2]
├── entry_date (DATE, NOT NULL — dátum účtovného prípadu) [IMPLEMENTED Phase 2]
├── description (TEXT, nullable) [IMPLEMENTED Phase 2]
├── created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, server_default now()) [IMPLEMENTED Phase 2]
├── created_by (VARCHAR(100), nullable) [IMPLEMENTED Phase 2]
├── posting_date (DATE — dátum zaúčtovania) [DEFERRED Phase 3+] — odlíšenie od entry_date
├── source (import | manual | system | correction) [DEFERRED Phase 4+] — zdroj zápisu
├── source_document_ref [DEFERRED Phase 3+] — väzba na source_document
├── is_storno (BOOLEAN) [DEFERRED Phase 4+] — storno mechanizmus
├── storno_of_id (FK → self) [DEFERRED Phase 4+] — storno mechanizmus
└── hash (SHA-256 chain — integrita zápisu) [DEFERRED Phase 5+] — immutability chain
UNIQUE: (entry_number) — uq_journal_entry_entry_number

journal_entry_line
├── line_id (PK, SERIAL) [IMPLEMENTED Phase 3]
├── entry_id (INTEGER, NOT NULL, FK → journal_entry, ON DELETE CASCADE) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: journal_entry_id)
├── line_number (SMALLINT, NOT NULL) [IMPLEMENTED Phase 3] — poradové číslo riadku v zápise
├── account_id (INTEGER, NOT NULL, FK → account, ON DELETE RESTRICT) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: FK → chart_of_accounts — opravené na account)
├── partner_id (INTEGER, nullable, FK → business_partner, ON DELETE SET NULL) [IMPLEMENTED Phase 3] — pre KV DPH
├── tax_rate_id (INTEGER, nullable, FK → tax_rate, ON DELETE SET NULL) [IMPLEMENTED Phase 3] — nahradil denormalizované vat_rate/vat_amount
├── debit_amount (NUMERIC(15,2), server_default 0) [IMPLEMENTED Phase 3]
├── credit_amount (NUMERIC(15,2), server_default 0) [IMPLEMENTED Phase 3]
├── description (TEXT, nullable) [IMPLEMENTED Phase 3] (DESIGN.md pôvodne: line_description)
├── currency_code (VARCHAR(3), NOT NULL, FK → currency, ON DELETE RESTRICT) [IMPLEMENTED Phase 3] — nahradil denormalizovaný currency string
├── vat_rate (nullable) [DEFERRED Phase 4+] — nahradené tax_rate_id FK (lepšia normalizácia)
└── vat_amount (nullable) [DEFERRED Phase 4+] — nahradené tax_rate_id FK (lepšia normalizácia)
UNIQUE: (entry_id, line_number) — uq_entry_line_number

import_batch
├── batch_id (PK, SERIAL)
├── filename (VARCHAR(500), NOT NULL)
├── file_hash (VARCHAR(64), NOT NULL, UNIQUE -- SHA-256 hex)
├── imported_at (TIMESTAMP WITH TIME ZONE, NOT NULL, server_default now())
├── imported_by (VARCHAR(100), nullable)
├── row_count (INTEGER, nullable)
├── status (VARCHAR(20), NOT NULL, CHECK IN pending/validated/imported/rejected)
└── validation_report (JSONB, nullable)

report_definition
├── id (PK)
├── report_type (balance_sheet | profit_loss | vat_return | ...)
├── version (legislatívna verzia)
├── valid_from, valid_to
└── line_mappings (JSONB — formuly pre výpočet riadkov)

generated_report
├── id (PK)
├── report_definition_id (FK)
├── period_id (FK)
├── generated_at
├── data (JSONB — vypočítané hodnoty)
├── pdf_path, xml_path
├── status (draft | final | submitted)
└── submission_id (FK → fs_submission)

fs_submission
├── id (PK)
├── report_id (FK)
├── submission_type (vat_return | vat_control | income_tax | ...)
├── xml_content (XML)
├── xml_hash (SHA-256)
├── signed_at, signed_by
├── submitted_at
├── fs_reference_number
├── fs_response (JSONB)
└── status (prepared | signed | submitted | accepted | rejected)

business_partner
├── partner_id (PK, SERIAL)
├── partner_type (VARCHAR(20), NOT NULL, CHECK IN ('CUSTOMER','SUPPLIER','BOTH'))
├── code (VARCHAR(50), UNIQUE)
├── name (VARCHAR(200), NOT NULL)
├── tax_id (VARCHAR(20), nullable)  — slovensky: IČO
├── vat_number (VARCHAR(20), nullable)  — slovensky: IČ DPH
├── address (TEXT, nullable)
├── contact_person (VARCHAR(100), nullable)
├── email (VARCHAR(100), nullable)
├── phone (VARCHAR(50), nullable)
└── is_active (BOOLEAN, NOT NULL, server_default TRUE)
Poznámka: Implementácia používa anglické názvy (tax_id, vat_number).
DESIGN.md pôvodne používal slovenské (ico, dic, ic_dph). Mapovanie:
  ico → tax_id, ic_dph → vat_number. Stĺpec dic nie je samostatný —
  v SK kontexte DIČ = daňové identifikačné číslo, riešené cez tax_id.
  country_code nie je implementovaný — pridať v budúcej fáze ak potrebné.
```

**Databázové constrainty:**
- `CHECK (debit_amount >= 0 AND credit_amount >= 0)`
- `CHECK (debit_amount = 0 OR credit_amount = 0)` — riadok je buď MD alebo D
- Trigger: SUM(debit) = SUM(credit) per journal_entry — double-entry enforcement
- `CHECK (debit_balance >= 0 AND credit_balance >= 0)` — opening_balance
- Unique: (tenant, period, entry_number) — sekvenčná integrita
- Unique: (period_id, account_id) na opening_balance — jeden počiatočný stav per účet per obdobie

## 5b. SERVICE LAYER (Business Logic)

### JournalEntryService

- `validate_double_entry(session, entry_id)` → `bool` — overuje Σ debit == Σ credit (SQL aggregácia func.sum + coalesce, Decimal presnosť). Raises ValueError ak nebalancované alebo prázdne.
- `get_entry_balance(session, entry_id)` → `(Decimal, Decimal)` — vráti (total_debit, total_credit). Vráti (Decimal("0.00"), Decimal("0.00")) pre entries bez riadkov.

### ImportService

- `create_batch(session, filename, file_hash, imported_by)` → `ImportBatch` — vytvorí novú importnú dávku so statusom 'pending'
- `update_batch_status(session, batch_id, status, validation_report, row_count)` → `ImportBatch` — aktualizuje status dávky [DEFERRED: state machine validácia prechodov — W-04]

### AccountService

- `recalculate_balance(session, account_id)` → `Account` — prepočíta current_balance: opening_balance + Σdebit - Σcredit (SQL func.sum) [DEFERRED: account_type normal_balance awareness — W-05]
- `get_account_statement(session, account_id, from_date, to_date)` → `list[dict]` — výpis účtu s running balance, inclusive date range

### Service Layer Conventions

- **Session parameter:** caller owns transaction, service NEVER calls commit() — len flush()
- **Decimal precision:** Numeric(15,2) v DB, func.sum()/func.coalesce() v SQL, Decimal v Pythone
- **Error handling:** ValueError pre nevalidné vstupy (not found, empty entries, unbalanced)
- **No side effects:** Services nemodifikujú iné entity mimo scope operácie

## 6. REST API ARCHITECTURE

### 6.1 Conventions

| Parameter | Hodnota |
|-----------|---------|
| Framework | FastAPI (Python 3.12) |
| ORM | SQLAlchemy 2.0 (SYNC) |
| DB Driver | pg8000 (SYNC) |
| Validation | Pydantic v2 |
| Base URL | `http://localhost:9180/api/v1` |
| Endpoint functions | `def` (NIKDY `async def`) — sync DB cez threadpool |
| Database session | sync `get_db()` dependency (yields Session) |
| CORS | enabled pre `http://localhost:9182` (frontend), `http://localhost:5173` (Vite dev) |

### 6.2 File Structure

```
app/
├── main.py                          (FastAPI app, router includes, CORS, /health)
├── database.py                      (engine, SessionLocal, get_db — EXISTS)
├── routers/
│   ├── __init__.py
│   ├── currencies.py
│   ├── account_types.py
│   ├── tax_rates.py
│   ├── business_partners.py
│   ├── charts_of_accounts.py
│   ├── import_batches.py
│   ├── accounting_periods.py
│   ├── accounts.py
│   ├── journal_entries.py           (includes nested /lines endpoints)
│   ├── opening_balances.py
│   ├── source_documents.py
│   └── document_entry_links.py
├── schemas/
│   ├── __init__.py
│   ├── common.py                    (PaginatedResponse generic)
│   ├── currency.py
│   ├── account_type.py
│   ├── tax_rate.py
│   ├── business_partner.py
│   ├── chart_of_accounts.py
│   ├── import_batch.py
│   ├── accounting_period.py
│   ├── account.py
│   ├── journal_entry.py             (includes JournalEntryLine schemas)
│   ├── opening_balance.py
│   ├── source_document.py
│   └── document_entry_link.py
├── services/
│   ├── __init__.py
│   ├── journal_entry_service.py     (EXISTS — extend)
│   ├── import_service.py            (EXISTS — extend)
│   ├── account_service.py           (EXISTS — extend)
│   ├── currency_service.py          (NEW)
│   ├── account_type_service.py      (NEW)
│   ├── tax_rate_service.py          (NEW)
│   ├── business_partner_service.py  (NEW)
│   ├── chart_of_accounts_service.py (NEW)
│   ├── accounting_period_service.py (NEW)
│   ├── opening_balance_service.py   (NEW)
│   ├── source_document_service.py   (NEW)
│   └── document_entry_link_service.py (NEW)
└── models/                          (EXISTS — no changes)
```

### 6.3 Pagination & List Response

Všetky list endpointy používajú jednotný pagination pattern:

Query parametre: `skip` (default 0), `limit` (default 50, max 100)

Response formát:
```json
{
  "items": [...],
  "total": 142,
  "skip": 0,
  "limit": 50
}
```

Generic Pydantic schema: `PaginatedResponse[T]` s `items: list[T]`, `total: int`, `skip: int`, `limit: int`.

### 6.4 Error Handling

| HTTP Status | Použitie |
|-------------|----------|
| 400 | Nevalidný vstup (validation error, business rule violation) |
| 404 | Entita nenájdená |
| 409 | Conflict (duplicate unique value, FK constraint violation) |
| 500 | Neočakávaná chyba |

Response formát: `{"detail": "Human-readable error message"}`

FastAPI validation errors (422) sú ponechané v default formáte.

### 6.5 Pydantic Schemas

Konvencie:
- `XxxCreate` — polia pre POST (bez PK, bez server-generated timestamps)
- `XxxRead` — všetky polia vrátane PK a timestamps, `model_config = ConfigDict(from_attributes=True)`
- `XxxUpdate` — editovateľné polia, všetky Optional
- Decimal polia: `Decimal` typ (nie float)
- Date polia: `date` typ
- Datetime polia: `datetime` typ

---

#### 6.5.1 Currency (PK: `currency_code` — natural key)

**CurrencyCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| currency_code | str (max 3) | áno | ISO 4217 |
| name | str (max 100) | áno | |
| symbol | str (max 10) | nie | €, $, Kč |
| decimal_places | int | nie | default 2 |
| is_active | bool | nie | default True |

**CurrencyRead:** všetky polia z Create + `updated_at` (datetime)

**CurrencyUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| name | str | nie |
| symbol | str | nie |
| decimal_places | int | nie |
| is_active | bool | nie |

Poznámka: `currency_code` sa neaktualizuje (natural PK).

---

#### 6.5.2 AccountType (PK: `account_type_id`)

**AccountTypeCreate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| code | str (max 20) | áno |
| name | str (max 100) | áno |
| description | str | nie |

**AccountTypeRead:** account_type_id (int) + všetky polia z Create

**AccountTypeUpdate:** všetky polia z Create ako Optional

---

#### 6.5.3 TaxRate (PK: `tax_rate_id`)

**TaxRateCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| code | str (max 20) | áno | VAT20, VAT10 |
| name | str (max 100) | áno | |
| rate | Decimal | áno | 0-100 |
| valid_from | date | nie | |
| valid_to | date | nie | |
| is_active | bool | nie | default True |

**TaxRateRead:** tax_rate_id (int) + všetky polia z Create

**TaxRateUpdate:** všetky polia z Create ako Optional

---

#### 6.5.4 BusinessPartner (PK: `partner_id`)

**BusinessPartnerCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| partner_type | str | áno | CUSTOMER / SUPPLIER / BOTH |
| code | str (max 50) | nie | unique |
| name | str (max 200) | áno | |
| tax_id | str (max 20) | nie | IČO |
| vat_number | str (max 20) | nie | IČ DPH |
| address | str | nie | |
| contact_person | str (max 100) | nie | |
| email | str (max 100) | nie | |
| phone | str (max 50) | nie | |
| is_active | bool | nie | default True |

**BusinessPartnerRead:** partner_id (int) + všetky polia z Create

**BusinessPartnerUpdate:** všetky polia z Create ako Optional

---

#### 6.5.5 ChartOfAccounts (PK: `chart_id`)

**ChartOfAccountsCreate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| code | str (max 20) | áno |
| name | str (max 100) | áno |
| description | str | nie |

**ChartOfAccountsRead:** chart_id (int) + všetky polia z Create

**ChartOfAccountsUpdate:** všetky polia z Create ako Optional

---

#### 6.5.6 ImportBatch (PK: `batch_id`)

**ImportBatchCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| filename | str (max 500) | áno | |
| file_hash | str (max 64) | áno | SHA-256 hex, unique |
| imported_by | str (max 100) | nie | |

**ImportBatchRead:**

| Pole | Typ | Poznámka |
|------|-----|----------|
| batch_id | int | PK |
| filename | str | |
| file_hash | str | |
| imported_at | datetime | server-generated |
| imported_by | str | nullable |
| row_count | int | nullable |
| status | str | pending/validated/imported/rejected |
| validation_report | dict | nullable, JSONB |

**ImportBatchUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| row_count | int | nie |
| imported_by | str | nie |

Poznámka: `status` sa neaktualizuje cez PUT — len cez špeciálne action endpointy (6.7).

---

#### 6.5.7 AccountingPeriod (PK: `period_id`)

**AccountingPeriodCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| chart_id | int | áno | FK → chart_of_accounts |
| year | int | áno | 2025, 2026, ... |
| period_number | int | áno | 1-13 (13=uzávierka) |
| start_date | date | áno | |
| end_date | date | áno | |
| is_closed | bool | nie | default False |

**AccountingPeriodRead:** period_id (int) + všetky polia z Create

**AccountingPeriodUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| start_date | date | nie |
| end_date | date | nie |
| is_closed | bool | nie |

Poznámka: `chart_id`, `year`, `period_number` sa neaktualizujú (súčasť unique composite key).

---

#### 6.5.8 Account (PK: `account_id`)

**AccountCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| chart_id | int | áno | FK → chart_of_accounts |
| account_number | str (max 20) | áno | napr. '343000' |
| name | str (max 200) | áno | |
| account_type_id | int | áno | FK → account_type |
| currency_code | str (max 3) | áno | FK → currency |
| parent_account_id | int | nie | FK → self (analytika) |
| level | int | áno | hierarchy depth: 1=root |
| is_active | bool | nie | default True |
| opening_balance | Decimal | nie | default 0 |

**AccountRead:**

| Pole | Typ | Poznámka |
|------|-----|----------|
| account_id | int | PK |
| chart_id | int | |
| account_number | str | |
| name | str | |
| account_type_id | int | |
| currency_code | str | |
| parent_account_id | int | nullable |
| level | int | |
| is_active | bool | |
| opening_balance | Decimal | |
| current_balance | Decimal | server-calculated |
| updated_at | datetime | |

**AccountUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| name | str | nie |
| account_type_id | int | nie |
| currency_code | str | nie |
| parent_account_id | int | nie |
| level | int | nie |
| is_active | bool | nie |

Poznámka: `chart_id` a `account_number` sa neaktualizujú (súčasť unique composite key). `current_balance` sa neaktualizuje cez PUT — len cez recalculate endpoint (6.7).

---

#### 6.5.9 JournalEntry (PK: `entry_id`)

**JournalEntryCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| entry_number | str (max 50) | áno | unique |
| entry_date | date | áno | dátum účtovného prípadu |
| description | str | nie | |
| batch_id | int | nie | FK → import_batch, nullable |
| created_by | str (max 100) | nie | |
| lines | list[JournalEntryLineCreate] | áno | min 2 riadky (double-entry) |

**JournalEntryRead:**

| Pole | Typ | Poznámka |
|------|-----|----------|
| entry_id | int | PK |
| entry_number | str | |
| entry_date | date | |
| description | str | nullable |
| batch_id | int | nullable |
| created_at | datetime | server-generated |
| created_by | str | nullable |
| lines | list[JournalEntryLineRead] | nested |

**JournalEntryUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| entry_date | date | nie |
| description | str | nie |

Poznámka: `entry_number` sa neaktualizuje (immutable journal princíp). Lines sa spravujú cez nested endpointy (6.6).

---

#### 6.5.10 JournalEntryLine (PK: `line_id`) — nested pod JournalEntry

**JournalEntryLineCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| line_number | int | áno | poradové číslo v zápise |
| account_id | int | áno | FK → account |
| partner_id | int | nie | FK → business_partner |
| tax_rate_id | int | nie | FK → tax_rate |
| debit_amount | Decimal | nie | default 0 |
| credit_amount | Decimal | nie | default 0 |
| description | str | nie | |
| currency_code | str (max 3) | áno | FK → currency |

Poznámka: `entry_id` sa nepredáva v body — odvodzuje sa z URL path parametra.

**JournalEntryLineRead:**

| Pole | Typ | Poznámka |
|------|-----|----------|
| line_id | int | PK |
| entry_id | int | |
| line_number | int | |
| account_id | int | |
| partner_id | int | nullable |
| tax_rate_id | int | nullable |
| debit_amount | Decimal | |
| credit_amount | Decimal | |
| description | str | nullable |
| currency_code | str | |

**JournalEntryLineUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| account_id | int | nie |
| partner_id | int | nie |
| tax_rate_id | int | nie |
| debit_amount | Decimal | nie |
| credit_amount | Decimal | nie |
| description | str | nie |
| currency_code | str | nie |

Poznámka: `line_number` sa neaktualizuje.

---

#### 6.5.11 OpeningBalance (PK: `balance_id`)

**OpeningBalanceCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| period_id | int | áno | FK → accounting_period |
| account_id | int | áno | FK → account |
| debit_amount | Decimal | nie | default 0 |
| credit_amount | Decimal | nie | default 0 |

**OpeningBalanceRead:** balance_id (int) + všetky polia z Create + `created_at` (datetime)

**OpeningBalanceUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| debit_amount | Decimal | nie |
| credit_amount | Decimal | nie |

Poznámka: `period_id` a `account_id` sa neaktualizujú (súčasť unique composite key).

---

#### 6.5.12 SourceDocument (PK: `document_id`)

**SourceDocumentCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| document_type | str | áno | issued_invoice / received_invoice / cash_receipt |
| document_number | str (max 50) | áno | unique |
| issue_date | date | áno | |
| partner_id | int | áno | FK → business_partner |
| total_amount | Decimal | áno | |
| currency_code | str (max 3) | áno | FK → currency |

**SourceDocumentRead:** document_id (int) + všetky polia z Create + `created_at` (datetime)

**SourceDocumentUpdate:**

| Pole | Typ | Povinné |
|------|-----|---------|
| document_type | str | nie |
| document_number | str | nie |
| issue_date | date | nie |
| partner_id | int | nie |
| total_amount | Decimal | nie |
| currency_code | str | nie |

---

#### 6.5.13 DocumentEntryLink (PK: `link_id`)

**DocumentEntryLinkCreate:**

| Pole | Typ | Povinné | Poznámka |
|------|-----|---------|----------|
| document_id | int | áno | FK → source_document |
| entry_id | int | áno | FK → journal_entry |

**DocumentEntryLinkRead:** link_id (int) + document_id (int) + entry_id (int) + `created_at` (datetime)

**Žiadny Update schema** — link sa vytvára alebo maže, nikdy neaktualizuje.

---

### 6.6 CRUD Endpoints

Štandardný CRUD pattern pre každú entitu. URL resource names v kebab-case.

#### Flat Resources (12 entít)

| Resource | URL prefix | PK parameter |
|----------|------------|--------------|
| Currency | `/api/v1/currencies` | `{currency_code}` (str) |
| AccountType | `/api/v1/account-types` | `{account_type_id}` (int) |
| TaxRate | `/api/v1/tax-rates` | `{tax_rate_id}` (int) |
| BusinessPartner | `/api/v1/business-partners` | `{partner_id}` (int) |
| ChartOfAccounts | `/api/v1/charts-of-accounts` | `{chart_id}` (int) |
| ImportBatch | `/api/v1/import-batches` | `{batch_id}` (int) |
| AccountingPeriod | `/api/v1/accounting-periods` | `{period_id}` (int) |
| Account | `/api/v1/accounts` | `{account_id}` (int) |
| JournalEntry | `/api/v1/journal-entries` | `{entry_id}` (int) |
| OpeningBalance | `/api/v1/opening-balances` | `{balance_id}` (int) |
| SourceDocument | `/api/v1/source-documents` | `{document_id}` (int) |
| DocumentEntryLink | `/api/v1/document-entry-links` | `{link_id}` (int) |

Operácie per resource:

| Metóda | URL | Popis | Request Body | Response |
|--------|-----|-------|-------------|----------|
| GET | `/{resource}` | List (paginated) | — | PaginatedResponse[XxxRead] |
| GET | `/{resource}/{pk}` | Get by PK | — | XxxRead |
| POST | `/{resource}` | Create | XxxCreate | XxxRead (201) |
| PUT | `/{resource}/{pk}` | Update | XxxUpdate | XxxRead |
| DELETE | `/{resource}/{pk}` | Delete | — | 204 No Content |

Výnimka: DocumentEntryLink nemá PUT endpoint (žiadny Update schema).

#### Nested Resource: JournalEntryLine

| Metóda | URL | Popis | Request Body | Response |
|--------|-----|-------|-------------|----------|
| GET | `/api/v1/journal-entries/{entry_id}/lines` | List lines | — | list[JournalEntryLineRead] |
| GET | `/api/v1/journal-entries/{entry_id}/lines/{line_id}` | Get line | — | JournalEntryLineRead |
| POST | `/api/v1/journal-entries/{entry_id}/lines` | Add line | JournalEntryLineCreate | JournalEntryLineRead (201) |
| PUT | `/api/v1/journal-entries/{entry_id}/lines/{line_id}` | Update line | JournalEntryLineUpdate | JournalEntryLineRead |
| DELETE | `/api/v1/journal-entries/{entry_id}/lines/{line_id}` | Delete line | — | 204 No Content |

Poznámka: Lines sa vytvárajú aj atomicky v rámci POST `/api/v1/journal-entries` (cez `lines` pole v JournalEntryCreate). Nested endpointy slúžia na individuálnu správu riadkov existujúceho zápisu.

#### List Endpoint Filtre

Okrem `skip` a `limit` každý list endpoint podporuje filtre relevantné pre danú entitu:

| Resource | Filter parametre |
|----------|-----------------|
| Currency | `is_active` (bool) |
| AccountType | — |
| TaxRate | `is_active` (bool) |
| BusinessPartner | `is_active` (bool), `partner_type` (str) |
| ChartOfAccounts | — |
| ImportBatch | `status` (str) |
| AccountingPeriod | `chart_id` (int), `year` (int), `is_closed` (bool) |
| Account | `chart_id` (int), `account_type_id` (int), `is_active` (bool), `parent_account_id` (int) |
| JournalEntry | `batch_id` (int), `entry_date_from` (date), `entry_date_to` (date) |
| OpeningBalance | `period_id` (int), `account_id` (int) |
| SourceDocument | `document_type` (str), `partner_id` (int), `issue_date_from` (date), `issue_date_to` (date) |
| DocumentEntryLink | `document_id` (int), `entry_id` (int) |

Všetky filtre sú Optional query parametre.

### 6.7 Special Endpoints (Business Logic)

Nad rámec štandardného CRUD — endpointy mapované na existujúce service metódy.

#### JournalEntryService Endpoints

| Metóda | URL | Popis | Response |
|--------|-----|-------|----------|
| GET | `/api/v1/journal-entries/{entry_id}/validate` | Double-entry validácia (Σ debit == Σ credit) | `{"valid": bool, "total_debit": str, "total_credit": str, "difference": str}` |
| GET | `/api/v1/journal-entries/{entry_id}/balance` | Get entry balance | `{"total_debit": str, "total_credit": str}` |

Poznámka: Decimal hodnoty v JSON response ako string (zachovanie presnosti).

#### AccountService Endpoints

| Metóda | URL | Popis | Response |
|--------|-----|-------|----------|
| POST | `/api/v1/accounts/{account_id}/recalculate-balance` | Prepočíta current_balance | AccountRead (aktualizovaný) |
| GET | `/api/v1/accounts/{account_id}/statement` | Výpis účtu | `{"account_id": int, "from_date": str, "to_date": str, "opening_balance": str, "entries": list[StatementEntry], "closing_balance": str}` |

Statement query parametre: `from_date` (date, povinný), `to_date` (date, povinný)

StatementEntry:

| Pole | Typ |
|------|-----|
| entry_date | date |
| entry_number | str |
| description | str |
| debit_amount | Decimal (str) |
| credit_amount | Decimal (str) |
| running_balance | Decimal (str) |

#### ImportService Endpoints (batch status transitions)

| Metóda | URL | Popis | Response |
|--------|-----|-------|----------|
| POST | `/api/v1/import-batches/{batch_id}/validate` | Transition: pending → validated | ImportBatchRead |
| POST | `/api/v1/import-batches/{batch_id}/import` | Transition: validated → imported | ImportBatchRead |
| POST | `/api/v1/import-batches/{batch_id}/reject` | Transition: any → rejected | ImportBatchRead |

Request body pre validate/import (Optional):

| Pole | Typ | Poznámka |
|------|-----|----------|
| row_count | int | pre import: počet importovaných riadkov |
| validation_report | dict | pre validate: výsledok validácie |

Poznámka: State machine validácia prechodov je W-04 (deferred) — v prvej implementácii jednoduchý setter, state machine sa pridá neskôr.

### 6.8 Service Layer Extension

Existujúce 3 servisy sa rozšíria, 9 nových servisov pre zvyšné entity.

#### Existujúce servisy (EXTEND)

**JournalEntryService** — pridať CRUD metódy:
- `list_entries(session, skip, limit, filters)` → list[JournalEntry], total
- `get_entry(session, entry_id)` → JournalEntry (with lines eager-loaded)
- `create_entry(session, data)` → JournalEntry (atomicky s lines, double-entry validácia)
- `update_entry(session, entry_id, data)` → JournalEntry
- `delete_entry(session, entry_id)` → None
- `list_lines(session, entry_id)` → list[JournalEntryLine]
- `get_line(session, entry_id, line_id)` → JournalEntryLine
- `create_line(session, entry_id, data)` → JournalEntryLine
- `update_line(session, entry_id, line_id, data)` → JournalEntryLine
- `delete_line(session, entry_id, line_id)` → None
- `validate_double_entry(session, entry_id)` → bool (EXISTS)
- `get_entry_balance(session, entry_id)` → (Decimal, Decimal) (EXISTS)

**ImportService** — pridať CRUD metódy:
- `list_batches(session, skip, limit, filters)` → list[ImportBatch], total
- `get_batch(session, batch_id)` → ImportBatch
- `create_batch(session, filename, file_hash, imported_by)` → ImportBatch (EXISTS)
- `update_batch(session, batch_id, data)` → ImportBatch
- `delete_batch(session, batch_id)` → None
- `update_batch_status(session, batch_id, status, ...)` → ImportBatch (EXISTS)
- `validate_batch(session, batch_id, validation_report)` → ImportBatch (wraps update_batch_status)
- `import_batch(session, batch_id, row_count)` → ImportBatch (wraps update_batch_status)
- `reject_batch(session, batch_id)` → ImportBatch (wraps update_batch_status)

**AccountService** — pridať CRUD metódy:
- `list_accounts(session, skip, limit, filters)` → list[Account], total
- `get_account(session, account_id)` → Account
- `create_account(session, data)` → Account
- `update_account(session, account_id, data)` → Account
- `delete_account(session, account_id)` → None
- `recalculate_balance(session, account_id)` → Account (EXISTS)
- `get_account_statement(session, account_id, from_date, to_date)` → list[dict] (EXISTS)

#### Nové servisy (NEW) — CRUD only

Pre každý nový servis rovnaký pattern:
- `list_{entities}(session, skip, limit, filters)` → list[Model], total
- `get_{entity}(session, pk)` → Model
- `create_{entity}(session, data)` → Model
- `update_{entity}(session, pk, data)` → Model
- `delete_{entity}(session, pk)` → None

| Servis | Model | PK |
|--------|-------|-----|
| CurrencyService | Currency | currency_code (str) |
| AccountTypeService | AccountType | account_type_id (int) |
| TaxRateService | TaxRate | tax_rate_id (int) |
| BusinessPartnerService | BusinessPartner | partner_id (int) |
| ChartOfAccountsService | ChartOfAccounts | chart_id (int) |
| AccountingPeriodService | AccountingPeriod | period_id (int) |
| OpeningBalanceService | OpeningBalance | balance_id (int) |
| SourceDocumentService | SourceDocument | document_id (int) |
| DocumentEntryLinkService | DocumentEntryLink | link_id (int) |

Service layer conventions (z Section 5b — platia aj pre nové servisy):
- Session parameter: caller owns transaction, service NEVER calls commit() — len flush()
- Error handling: ValueError pre nevalidné vstupy (not found, duplicate, FK violation)
- No side effects: Services nemodifikujú iné entity mimo scope operácie

### 6.9 Router Registration

```python
# app/main.py
app.include_router(currencies.router, prefix="/api/v1/currencies", tags=["Currencies"])
app.include_router(account_types.router, prefix="/api/v1/account-types", tags=["Account Types"])
app.include_router(tax_rates.router, prefix="/api/v1/tax-rates", tags=["Tax Rates"])
app.include_router(business_partners.router, prefix="/api/v1/business-partners", tags=["Business Partners"])
app.include_router(charts_of_accounts.router, prefix="/api/v1/charts-of-accounts", tags=["Charts of Accounts"])
app.include_router(import_batches.router, prefix="/api/v1/import-batches", tags=["Import Batches"])
app.include_router(accounting_periods.router, prefix="/api/v1/accounting-periods", tags=["Accounting Periods"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(journal_entries.router, prefix="/api/v1/journal-entries", tags=["Journal Entries"])
app.include_router(opening_balances.router, prefix="/api/v1/opening-balances", tags=["Opening Balances"])
app.include_router(source_documents.router, prefix="/api/v1/source-documents", tags=["Source Documents"])
app.include_router(document_entry_links.router, prefix="/api/v1/document-entry-links", tags=["Document Entry Links"])
```

FastAPI auto-generated docs: `http://localhost:9180/docs` (Swagger UI)

## 7. FRONTEND ARCHITECTURE

### 7.1 Tech Stack

| Technológia | Verzia | Účel |
|-------------|--------|------|
| React | 18 | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 5.x | Build tool + dev server |
| Tailwind CSS | 3.x | Utility-first styling |
| React Router | v6 | Client-side routing |
| TanStack Query | v5 | Server state management (data fetching, caching, mutations) |
| Axios | 1.x | HTTP client |

### 7.2 Port Assignment

| Prostredie | Port |
|------------|------|
| Vite dev server | 5173 (default) |
| Production (Docker/Nginx) | 9182 |

### 7.3 File Structure

```
src/
├── api/
│   ├── client.ts                    (Axios instance, base URL, interceptors)
│   ├── currencies.ts
│   ├── accountTypes.ts
│   ├── taxRates.ts
│   ├── businessPartners.ts
│   ├── chartsOfAccounts.ts
│   ├── importBatches.ts
│   ├── accountingPeriods.ts
│   ├── accounts.ts
│   ├── journalEntries.ts           (includes line API functions)
│   ├── openingBalances.ts
│   ├── sourceDocuments.ts
│   └── documentEntryLinks.ts
├── components/
│   ├── layout/
│   │   ├── Layout.tsx               (Sidebar + Header + main content area)
│   │   ├── Sidebar.tsx              (navigation, grouped entity links)
│   │   └── Header.tsx               (page title, breadcrumbs)
│   └── shared/
│       ├── DataTable.tsx            (generic table, sorting, column config)
│       ├── Pagination.tsx           (skip/limit controls)
│       ├── FormField.tsx            (label + input + error wrapper)
│       ├── Modal.tsx                (confirmation dialogs)
│       ├── Button.tsx               (primary, secondary, danger variants)
│       ├── Input.tsx                (text, number, date inputs)
│       ├── Select.tsx               (dropdown for FK references)
│       ├── LoadingSpinner.tsx
│       └── ErrorMessage.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── currencies/
│   │   ├── CurrencyListPage.tsx
│   │   ├── CurrencyFormPage.tsx     (create + edit mode)
│   │   └── CurrencyDetailPage.tsx
│   ├── accountTypes/
│   │   ├── AccountTypeListPage.tsx
│   │   ├── AccountTypeFormPage.tsx
│   │   └── AccountTypeDetailPage.tsx
│   ├── taxRates/
│   │   ├── TaxRateListPage.tsx
│   │   ├── TaxRateFormPage.tsx
│   │   └── TaxRateDetailPage.tsx
│   ├── businessPartners/
│   │   ├── BusinessPartnerListPage.tsx
│   │   ├── BusinessPartnerFormPage.tsx
│   │   └── BusinessPartnerDetailPage.tsx
│   ├── chartsOfAccounts/
│   │   ├── ChartOfAccountsListPage.tsx
│   │   ├── ChartOfAccountsFormPage.tsx
│   │   └── ChartOfAccountsDetailPage.tsx
│   ├── importBatches/
│   │   ├── ImportBatchListPage.tsx
│   │   ├── ImportBatchFormPage.tsx
│   │   └── ImportBatchDetailPage.tsx  (includes status action buttons)
│   ├── accountingPeriods/
│   │   ├── AccountingPeriodListPage.tsx
│   │   ├── AccountingPeriodFormPage.tsx
│   │   └── AccountingPeriodDetailPage.tsx
│   ├── accounts/
│   │   ├── AccountListPage.tsx
│   │   ├── AccountFormPage.tsx
│   │   └── AccountDetailPage.tsx      (includes recalculate + statement)
│   ├── journalEntries/
│   │   ├── JournalEntryListPage.tsx
│   │   ├── JournalEntryFormPage.tsx   (includes inline line editor)
│   │   └── JournalEntryDetailPage.tsx (includes lines table + validate/balance)
│   ├── openingBalances/
│   │   ├── OpeningBalanceListPage.tsx
│   │   ├── OpeningBalanceFormPage.tsx
│   │   └── OpeningBalanceDetailPage.tsx
│   └── sourceDocuments/
│       ├── SourceDocumentListPage.tsx
│       ├── SourceDocumentFormPage.tsx
│       └── SourceDocumentDetailPage.tsx (includes linked entries section)
├── types/
│   ├── common.ts                    (PaginatedResponse<T>, filter types)
│   ├── currency.ts
│   ├── accountType.ts
│   ├── taxRate.ts
│   ├── businessPartner.ts
│   ├── chartOfAccounts.ts
│   ├── importBatch.ts
│   ├── accountingPeriod.ts
│   ├── account.ts
│   ├── journalEntry.ts             (includes JournalEntryLine types)
│   ├── openingBalance.ts
│   ├── sourceDocument.ts
│   └── documentEntryLink.ts
├── hooks/
│   ├── useCurrencies.ts            (TanStack Query hooks: useList, useGet, useCreate, useUpdate, useDelete)
│   ├── useAccountTypes.ts
│   ├── useTaxRates.ts
│   ├── useBusinessPartners.ts
│   ├── useChartsOfAccounts.ts
│   ├── useImportBatches.ts
│   ├── useAccountingPeriods.ts
│   ├── useAccounts.ts              (includes useRecalculateBalance, useAccountStatement)
│   ├── useJournalEntries.ts        (includes useValidate, useBalance, line hooks)
│   ├── useOpeningBalances.ts
│   ├── useSourceDocuments.ts
│   └── useDocumentEntryLinks.ts
├── App.tsx                          (QueryClientProvider + RouterProvider)
├── main.tsx                         (React root render)
└── router.tsx                       (React Router v6 route definitions)
```

### 7.4 Routing

```
/                                    → Dashboard
/currencies                          → CurrencyListPage
/currencies/new                      → CurrencyFormPage (create)
/currencies/:code                    → CurrencyDetailPage
/currencies/:code/edit               → CurrencyFormPage (edit)

/account-types                       → AccountTypeListPage
/account-types/new                   → AccountTypeFormPage (create)
/account-types/:id                   → AccountTypeDetailPage
/account-types/:id/edit              → AccountTypeFormPage (edit)

/tax-rates                           → TaxRateListPage
/tax-rates/new                       → TaxRateFormPage (create)
/tax-rates/:id                       → TaxRateDetailPage
/tax-rates/:id/edit                  → TaxRateFormPage (edit)

/business-partners                   → BusinessPartnerListPage
/business-partners/new               → BusinessPartnerFormPage (create)
/business-partners/:id               → BusinessPartnerDetailPage
/business-partners/:id/edit          → BusinessPartnerFormPage (edit)

/charts-of-accounts                  → ChartOfAccountsListPage
/charts-of-accounts/new              → ChartOfAccountsFormPage (create)
/charts-of-accounts/:id              → ChartOfAccountsDetailPage
/charts-of-accounts/:id/edit         → ChartOfAccountsFormPage (edit)

/import-batches                      → ImportBatchListPage
/import-batches/new                  → ImportBatchFormPage (create)
/import-batches/:id                  → ImportBatchDetailPage
/import-batches/:id/edit             → ImportBatchFormPage (edit)

/accounting-periods                  → AccountingPeriodListPage
/accounting-periods/new              → AccountingPeriodFormPage (create)
/accounting-periods/:id              → AccountingPeriodDetailPage
/accounting-periods/:id/edit         → AccountingPeriodFormPage (edit)

/accounts                            → AccountListPage
/accounts/new                        → AccountFormPage (create)
/accounts/:id                        → AccountDetailPage
/accounts/:id/edit                   → AccountFormPage (edit)

/journal-entries                     → JournalEntryListPage
/journal-entries/new                 → JournalEntryFormPage (create)
/journal-entries/:id                 → JournalEntryDetailPage
/journal-entries/:id/edit            → JournalEntryFormPage (edit)

/opening-balances                    → OpeningBalanceListPage
/opening-balances/new                → OpeningBalanceFormPage (create)
/opening-balances/:id                → OpeningBalanceDetailPage
/opening-balances/:id/edit           → OpeningBalanceFormPage (edit)

/source-documents                    → SourceDocumentListPage
/source-documents/new                → SourceDocumentFormPage (create)
/source-documents/:id                → SourceDocumentDetailPage
/source-documents/:id/edit           → SourceDocumentFormPage (edit)
```

Poznámka: DocumentEntryLink nemá vlastné pages — spravuje sa inline v SourceDocumentDetailPage a JournalEntryDetailPage.

### 7.5 Layout & Navigation

#### Sidebar Navigation (zoskupené)

```
DASHBOARD
─────────────────
HLAVNÁ KNIHA
  Účtové rozvrhy        /charts-of-accounts
  Účty                  /accounts
  Účtovné zápisy        /journal-entries
  Počiatočné stavy      /opening-balances
  Účtovné obdobia       /accounting-periods
─────────────────
DOKLADY
  Zdrojové doklady      /source-documents
─────────────────
IMPORT
  Import dávky          /import-batches
─────────────────
NASTAVENIA
  Obchodní partneri     /business-partners
  Meny                  /currencies
  Typy účtov            /account-types
  Sadzby DPH            /tax-rates
```

#### Layout Structure

```
+---------------------------------------------+
| Header (page title + breadcrumbs)           |
+----------+----------------------------------+
|          |                                  |
| Sidebar  |  Main Content Area               |
| (240px)  |  (List / Form / Detail page)     |
|          |                                  |
|          |                                  |
+----------+----------------------------------+
```

### 7.6 Page Patterns

#### List Page Pattern (pre každú entitu)
- Header: entity name + "Vytvoriť" button
- Filter panel: entity-specific filters (collapsible)
- DataTable: columns podľa entity, sortable headers
- Pagination: skip/limit controls
- Row actions: kliknutie → Detail page

#### Form Page Pattern (create + edit mode)
- Mode detection: `/new` = create, `/:id/edit` = edit (pre-fill z API)
- FormField per editovateľné pole
- FK polia: Select dropdown s dátami z API (TanStack Query)
- Validácia: client-side (required fields) + server-side (API errors)
- Actions: "Uložiť" + "Zrušiť" buttons
- Po uložení: redirect na Detail page

#### Detail Page Pattern (read-only view)
- Všetky polia entity v read-only formáte
- Action buttons: "Upraviť", "Vymazať" (s confirmation modal)
- Entity-specific action buttons (viď 7.7)

### 7.7 Entity-Specific Page Features

#### JournalEntryFormPage
- Inline line editor: tabuľka riadkov s add/remove/edit
- Minimálne 2 riadky (double-entry requirement)
- Automatický súčet MD/D s vizuálnou indikáciou balansu

#### JournalEntryDetailPage
- Lines tabuľka (read-only)
- "Validovať" button → volá validate endpoint, zobrazí výsledok
- "Zobraziť balance" → volá balance endpoint
- "Prepojené doklady" sekcia → DocumentEntryLinks (read-only, link na SourceDocument)

#### AccountDetailPage
- "Prepočítať saldo" button → volá recalculate-balance endpoint
- "Výpis účtu" sekcia → date range picker + statement tabuľka

#### ImportBatchDetailPage
- Status badge (farebný podľa stavu)
- Status action buttons (podľa aktuálneho stavu):
  - pending → "Validovať" button
  - validated → "Importovať" button
  - any (okrem rejected) → "Odmietnuť" button
- Validation report viewer (JSON → readable format)

#### SourceDocumentDetailPage
- "Prepojené zápisy" sekcia → DocumentEntryLinks
- "Prepojiť zápis" button → modal s výberom JournalEntry → vytvorí DocumentEntryLink

### 7.8 API Client

Axios instance (`src/api/client.ts`):
- baseURL: `http://localhost:9180/api/v1`
- Default headers: `Content-Type: application/json`
- Response interceptor: error handling (toast notifications pre 4xx/5xx)

Per-entity API module pattern (`src/api/{entity}.ts`):
- `list(params)` → GET list endpoint
- `getById(pk)` → GET detail endpoint
- `create(data)` → POST create endpoint
- `update(pk, data)` → PUT update endpoint
- `remove(pk)` → DELETE endpoint
- Entity-specific functions (validate, recalculate, etc.)

### 7.9 TypeScript Types

Mirrors Pydantic schemas (`src/types/{entity}.ts`):
- `interface XxxCreate { ... }` — request body pre POST
- `interface XxxRead { ... }` — response type
- `interface XxxUpdate { ... }` — request body pre PUT (Partial<XxxCreate> pattern)
- `interface PaginatedResponse<T> { items: T[]; total: number; skip: number; limit: number; }`

Decimal polia: `string` typ v TypeScript (server posiela ako string pre presnosť).
Date polia: `string` typ (ISO format, parsing na klientovi podľa potreby).

### 7.10 State Management

- **Server state:** TanStack Query (fetching, caching, mutations, refetching)
- **UI state:** React useState (form inputs, modal visibility, filter panel state)
- **Žiadny Redux/Zustand** — TanStack Query pokrýva všetky server-state potreby

TanStack Query hook pattern per entity (`src/hooks/use{Entity}.ts`):
- `use{Entity}List(filters)` — useQuery pre list endpoint
- `use{Entity}(pk)` — useQuery pre detail endpoint
- `useCreate{Entity}()` — useMutation pre POST
- `useUpdate{Entity}()` — useMutation pre PUT
- `useDelete{Entity}()` — useMutation pre DELETE
- Cache invalidation: mutation success → invalidate list query

### 7.11 Styling

- Tailwind CSS utility classes only
- Žiadne custom CSS files (okrem Tailwind base/components/utilities import)
- Responsive: sidebar collapsible na mobile (< 768px)
- Color scheme: light mode (default), dark mode support via Tailwind dark: prefix

## 8. WORKFLOW — YEAR-END PIPELINE

```
1. IMPORT           Excel denník z NEX Genesis
       ↓
2. AI VALIDATE      Ollama kontrola konzistencie + anomálií
       ↓
3. RECONCILE        Automatické odsúhlasenie (MD=D, salda)
       ↓
4. CLOSE BOOKS      Uzavretie účtovných kníh (uzávierkové operácie)
       ↓
5. GENERATE         Súvaha + VZaS + Poznámky + DP PO + DPH výkazy
       ↓
6. AI REVIEW        Finálna AI kontrola výkazov (cross-check, plausibility)
       ↓
7. SIGN             KEP podpísanie XML dokumentov
       ↓
8. SUBMIT           Elektronické podanie na portál FS
       ↓
9. CONFIRM          Potvrdenie prijatia od FS + archivácia
```

Zero-touch cieľ: Kroky 1-6 plne automatizované. Kroky 7-9 s human-in-the-loop (podpis vyžaduje explicitný súhlas).

## 9. PHASED IMPLEMENTATION

### VERSION 1.0.0 — Ročná účtovná závierka + DP PO (nahrádza externú účtovníčku)

Vstup: účtovný denník z NEX Genesis (Excel). Bez prvotných dokladov. Bez DPH. Scope: presne to, čo dnes robí externá účtovníčka — nič viac, nič menej.

**Phase 1 — Foundation (MVP)**
- Import Engine (Excel denník → DB)
- Ledger Core (immutable journal, chart of accounts, double-entry)
- Základný účtový rozvrh pre s.r.o.
- Opening balances import
- Základný dashboard (prehľad per tenant)

**Phase 2 — Reports + DP PO**
- Súvaha (Balance Sheet)
- Výkaz ziskov a strát (P&L)
- Hlavná kniha (report)
- Obratová predvaha
- Poznámky k ÚZ (Ollama AI draft + manuálna review)
- Daňové priznanie PO: plný výpočet + XML generovanie
- PDF + XLSX + XML export

**Phase 3 — FS Integration (DP PO + Účtovná závierka)**
- eID/KEP integrácia (eID občiansky preukaz + slovensko.sk)
- Podanie DP PO na portál FS
- Podanie účtovnej závierky do Registra účtovných závierok
- Spracovanie odpovedí od FS
- Archivácia podaní

→ **v1.0.0 RELEASE:** Kompletná náhrada externej účtovníčky

### VERSION 2.0.0 — DPH + Prvotné doklady + Three-Way Reconciliation

Rozšírenie o: DPH výkazy (nahrádza eDane), prvotné doklady (OF, DF, pokladňa).

**Phase 4 — DPH + eDane Replacement**
- DPH Priznanie: XML generovanie z NEX Genesis dát (nie výpočet)
- Kontrolný výkaz DPH: XML generovanie
- Súhrnný výkaz DPH: XML generovanie
- XSD validácia všetkých XML
- Podanie DPH výkazov na portál FS
- Nahradenie programu eDane

**Phase 5 — Source Documents Import**
- Import Engine rozšírenie: CSV/TXT kanál (Papaparse, cp852/utf-8)
- Source Documents modul (OF, DF, pokladňa)
- Automatické prelinkovanie: journal_entry ↔ source_document
- 3-úrovňový matching (deterministický → heuristický → AI)

**Phase 6 — Three-Way Reconciliation**
- 10 krížových kontrol (R1–R10)
- Reconciliation Report (PASS/WARN/FAIL)
- DPH krížová kontrola (KV vs. knihy OF/DF)

→ **v2.0.0 RELEASE:** DPH podanie + plný audit chain s verifikovanou konzistenciou

### VERSION 3.0.0 — AI Intelligence

**Phase 7 — AI + Automation**
- AI Validation Layer (Ollama)
- Anomaly detection + Pre-submission review
- Year-end pipeline orchestration
- Continuous Closing — mesačná auto-validácia + readiness score per tenant
- Merkle Tree Integrity — kryptografický dôkaz integrity účtovného obdobia
- One-Click Audit Package — ZIP export s hashom integrity

**Phase 8 — Advanced AI**
- Cross-Tenant Intelligence — medzifiremná AI analytika, inter-company reconciliation
- Regulatory Sandbox — simulácia dopadu legislatívnych zmien na všetkých 7 firiem
- Natural Language Querying — dopytovanie ledgera v slovenčine cez Ollama
- Accounting DNA — Confidence Score per journal entry (vyžaduje v2.0.0 prvotné doklady)
- Predictive Cash Flow — AI predikcia peňažných tokov na 30/60/90 dní

→ **v3.0.0 RELEASE:** AI-native accounting intelligence platform

## 10. BEZPEČNOSŤ

- Dáta: Schema-per-tenant izolácia, žiadny cross-tenant prístup
- Audit: Immutable audit trail, SHA-256 hash chain na journal entries
- Podpisy: KEP certifikáty v bezpečnom úložisku (Vaultwarden)
- AI: Ollama lokálny — žiadne účtovné dáta neopúšťajú ANDROS
- Prístup: Role-based (director, accountant, auditor — read-only)
- Zálohy: PostgreSQL WAL archiving + denný backup

## 11. LEGISLATÍVNE ZDROJE

- Zákon č. 431/2002 Z.z. o účtovníctve
- Opatrenie MF SR č. 23054/2002-92 (postupy účtovania pre podnikateľov)
- Opatrenie MF SR č. 4455/2003-92 (vzory účtovných výkazov)
- Zákon č. 595/2003 Z.z. o dani z príjmov
- Zákon č. 222/2004 Z.z. o DPH
- XML schémy: financnasprava.sk/sk/elektronicke-sluzby

## 12. INNOVATIVE FEATURES

### 12.1 Continuous Closing (v3.0.0 Phase 7)

Paradigma: Z ročného stresu na priebežnú pripravenosť.

Každý mesiac systém automaticky:
1. Uzavrie mesačné obdobie (soft-lock)
2. Spustí AI validáciu (kompletnosť zápisov, MD=D, odpisy, kurzové rozdiely)
3. Vygeneruje predbežné výkazy (Súvaha, VZaS)
4. Vypočíta Readiness Score per tenant (0–100%)

**Readiness Score indikátory:**
- Všetky mesačné obdobia uzavreté? (+20%)
- Odpisy zaúčtované? (+15%)
- Kurzové rozdiely vysporiadané? (+10%)
- Časové rozlíšenie kompletné? (+15%)
- DPH priznania podané? (+15%)
- Medziročná konzistencia OK? (+10%)
- AI anomálie vyriešené? (+15%)

Dashboard widget: "ICC s.r.o.: 92% ready | EM-1 s.r.o.: 78% ready — chýbajú odpisy za Q4"

### 12.2 Cross-Tenant Intelligence (v3.0.0 Phase 8)

Účel: Ollama analyzuje dáta naprieč všetkými 7 firmami súčasne.

**Funkcie:**
- Anomaly detection: Firma X má 3x vyššie admin náklady ako priemer ostatných — prečo?
- Inter-company reconciliation: Automatická identifikácia a odsúhlasenie transakcií medzi vlastnými firmami
- Pattern sharing: Ak AI nájde optimalizáciu pre jednu firmu, navrhne ju aj ostatným
- Konsolidovaný prehľad: Director dashboard so súhrnnými KPI naprieč všetkými firmami

Bezpečnosť: Funguje len na tenant úrovni directora — bežný accountant vidí len svoj tenant.

### 12.3 Regulatory Sandbox (v3.0.0 Phase 8)

Účel: Simulácia dopadu pripravovaných legislatívnych zmien pred ich účinnosťou.

**Workflow:**
1. Legislative Monitor detekuje novelu v legislatívnom procese (napr. zmena sadzby)
2. Systém vytvorí sandbox kópiu aktuálnych dát (read-only snapshot)
3. Aplikuje pripravovanú zmenu na sandbox
4. Prepočíta všetky výkazy a daňové povinnosti pre všetkých 7 tenantov
5. Generuje Impact Report: "Novela zvýši celkovú daňovú povinnosť o X € — rozpis per firma"

Hodnota: Mesiace na plánovanie namiesto dní. Strategické rozhodovanie na základe dát.

### 12.4 Natural Language Querying (v3.0.0 Phase 8)

Účel: Dopytovanie ledgera v slovenčine cez Ollama.

**Príklady:**
- "Aké boli celkové tržby za Q3 pre všetky firmy?"
- "Ktorá firma má najvyšší pomer záväzkov k aktívam?"
- "Porovnaj náklady na energie medziročne"
- "Ukáž mi všetky neuhradené faktúry nad 5000 €"

**Implementácia:**
1. Používateľ zadá otázku v slovenčine
2. Ollama preloží na SQL query (s whitelistom povolených tabuliek/operácií)
3. Query sa spustí (read-only, nikdy write)
4. Ollama sformátuje výsledok do čitateľnej odpovede + voliteľne graf/tabuľka

Bezpečnosť: SQL whitelist + read-only connection + tenant izolácia.

### 12.5 One-Click Audit Package (v3.0.0 Phase 7)

Účel: Kompletný audit balík na jedno kliknutie.

**Obsah ZIP:**
- Hlavná kniha (PDF + XLSX)
- Denník účtovných zápisov (PDF + XLSX)
- Obratová predvaha (PDF + XLSX)
- Účtovná závierka (Súvaha + VZaS + Poznámky) (PDF)
- Audit trail — kompletný log operácií (CSV)
- Zoznam účtovných zásad a metód (PDF)
- `MANIFEST.json` — zoznam súborov s SHA-256 hashom každého súboru
- `INTEGRITY.sig` — digitálny podpis celého balíka

Použitie: Daňová kontrola, externý audit, due diligence.

### 12.6 Accounting DNA — Confidence Score (v3.0.0 Phase 8)

Účel: Každá firma má unikátny účtovný "odtlačok" — typické vzory, sezónnosť, pomer nákladov. Ollama sa naučí tento fingerprint a každý nový zápis ohodnotí Confidence Score (0–100%).

**Učenie:**
- Po prvom roku: baseline model per tenant (minimálne 12 mesiacov dát)
- Vstupné features: účet, suma, partner, mesiac, deň v mesiaci, pomer MD/D, frekvencia
- Model: Ollama embeddings → vector similarity proti historickým zápisom v Qdrant

**Scoring:**
- 90–100% (zelená): Rutinná operácia, plne konzistentná s DNA → auto-accept
- 60–89% (žltá): Mierne nezvyčajné, ale v tolerancii → informačná notifikácia
- 0–59% (červená): Výrazná anomália → povinná review pred zaúčtovaním

**Príklady detekcie:**
- Faktúra na účet 518 (služby) od nového partnera za 15 000 € → score 25% (firma bežne účtuje služby do 2 000 €)
- Mesačný odpis 450 € na účet 551 → score 98% (identický každý mesiac)
- Účtovanie na účet 548 v januári → score 40% (firma historicky účtuje 548 len v Q4)

Adaptácia: Model sa retrainuje kvartálne. Schválené anomálie sa stávajú súčasťou DNA.

### 12.7 Predictive Cash Flow (v3.0.0 Phase 8)

Účel: AI predikcia peňažných tokov na 30/60/90 dní dopredu per tenant.

**Vstupné dáta (všetko z ledgera):**
- Historické príjmy a výdavky (sezónne vzory)
- Otvorené pohľadávky + priemerná doba inkasa per partner
- Otvorené záväzky + splatnosti
- Pravidelné fixné náklady (nájom, leasing, mzdy)
- DPH povinnosť (z Tax Engine)

**Výstup:**
- Cash flow projekcia per tenant (denná granularita)
- Alert systém: "EM-1 s.r.o. — za 45 dní cash gap 3 200 €"
- Cross-tenant view: Director vidí konsolidovaný cash flow všetkých 7 firiem
- Vizualizácia: graf s confidence intervalom (optimistický / realistický / pesimistický scenár)

Implementácia: Ollama + historické dáta. Nie je potrebný špecializovaný ML model — LLM vie extrapolovať vzory z účtovných dát s dostatočnou presnosťou pre SME segment.

### 12.8 Merkle Tree Integrity (v3.0.0 Phase 7)

Účel: Kryptografický dôkaz integrity celého účtovného obdobia — jeden hash = celý rok.

**Štruktúra:**

```
                    ROOT HASH (rok 2025)
                   /                    \
          H(Q1+Q2)                      H(Q3+Q4)
         /        \                    /        \
     H(M1+M2+M3)  H(M4+M5+M6)   H(M7+M8+M9)  H(M10+M11+M12)
       /  |  \
   H(JE1) H(JE2) ... H(JEn)

JE = Journal Entry hash (SHA-256)
H = SHA-256 parent hash
```

**Vlastnosti:**
- Leaf node = SHA-256 hash jednotlivého journal_entry (už máme v DB schéme)
- Mesačný hash = hash všetkých entries v mesiaci
- Kvartálny hash = hash mesačných hashov
- Root hash = hash kvartálnych hashov = integrita celého roka
- Akákoľvek zmena v akomkoľvek zápise zmení root hash

**Uloženie:**

```
merkle_node
├── id (PK)
├── period_id (FK)
├── level (entry | month | quarter | year)
├── period_key (napr. '2025', '2025-Q1', '2025-01')
├── hash (SHA-256)
├── left_child_id (FK → self)
├── right_child_id (FK → self)
├── computed_at
└── entry_count (počet leaf entries v podstrome)
```

**Verifikácia:**
- Pri uzávierke: systém vypočíta root hash a zapečatí
- Pri audite: recalculate root hash z entries → porovnaj so zapečateným → match = integrita OK
- Export: root hash + Merkle proof v One-Click Audit Package

Nadväznosť: Rovnaký pattern ako HMAC-SHA256 chain v orthodox-registry, povýšený na stromovú štruktúru pre efektívnu verifikáciu podmnožín.

### 12.9 FEATURES RESERVED FOR NEX AUTOMAT

Nasledovné features boli identifikované ako hodnotné, ale patria do plného účtovného modulu NEX Automat, nie do standalone NEX Ledger:

| Feature | Dôvod zaradenia do NEX Automat |
|---------|-------------------------------|
| Self-Healing Ledger | Vyžaduje hlbokú integráciu s ERP modulmi (majetok, sklady, mzdy) pre deterministické auto-opravy |
| Document Intelligence (OCR) | Skenovanie faktúr/dokladov je vstupná operácia ERP, nie funkcia ledgera |
| Compliance Passport | Real-time compliance status vyžaduje dáta z celého ERP (HR, obchod, dane), nie len z účtovníctva |

## 13. LEGISLATIVE COMPLIANCE ENGINE

### 13.1 Problém

Účtovná legislatíva sa mení každoročne — nové sadzby, zmeny vo výkazoch, nové XSD schémy FS. Systém MUSÍ byť vždy aktuálny, inak generuje neplatné výkazy.

### 13.2 Trojvrstvová architektúra (Three-Layer Compliance)

```
VRSTVA 1: MONITORING          Čo sa zmenilo?
    ↓
VRSTVA 2: ANALYSIS            Čo to znamená pre nás?
    ↓
VRSTVA 3: ADAPTATION          Ako systém reaguje?
```

### 13.3 Vrstva 1 — Legislative Monitoring

Zdroje dát (všetko in-house, zero external cost):

| Zdroj | Typ | Frekvencia | Metóda |
|-------|-----|------------|--------|
| Slov-Lex eZbierka | Zákony, novely (5-6 predpisov) | Denne | Web scraping (Playwright) + hash comparison |
| financnasprava.sk/XSD schémy | XSD schémy výkazov | Denne | Polling + SHA-256 hash comparison |
| MF SR vzory tlačív | Vzory výkazov | Denne | Web scraping + hash comparison |
| Finančné riaditeľstvo SR | Metodické pokyny | Denne | RSS/scraping |

Rozhodnutie: Externé služby (LexDATA a pod.) zamietnuté. ICC disponuje plným tech stackom na vlastné riešenie: Playwright (scraping), Ollama (AI analýza), Qdrant (fulltext), ANDROS (infra). Sledujeme presne 5-6 zákonov — general-purpose legislatívny monitoring je pre nás overengineering.

**Monitorované právne predpisy:**
- Zákon č. 431/2002 Z.z. o účtovníctve
- Zákon č. 595/2003 Z.z. o dani z príjmov
- Zákon č. 222/2004 Z.z. o DPH
- Opatrenie MF SR č. 23054/2002-92 (postupy účtovania)
- Opatrenie MF SR č. 4455/2003-92 (vzory výkazov)
- Súvisiace vyhlášky a nariadenia vlády

**Implementácia:**
- `LegislativeMonitor` — scheduled task (cron), beží denne
- Sťahuje nové verzie zákonov, XSD schém, vzorov výkazov
- Porovnáva hash s uloženou verziou
- Pri zmene vytvára `LegislativeChange` záznam v DB

### 13.4 Vrstva 2 — AI Impact Analysis (Ollama)

Účel: Keď monitoring detekuje zmenu, AI analyzuje dopad na NEX Ledger.

**Workflow:**
1. `LegislativeChange` záznam spúšťa AI analýzu
2. Ollama dostane: text novely + aktuálne report_definition mapovania + aktuálne daňové sadzby
3. AI identifikuje:
   - Zmenené čísla riadkov výkazov
   - Nové/zrušené účty v účtovom rozvrhu
   - Zmenené sadzby (daň z príjmov, DPH, odpisy)
   - Nové povinné prílohy alebo výkazy
   - Zmenené XSD schémy pre elektronické podanie
4. Výstup: `ImpactReport` (JSONB) s klasifikáciou:
   - AUTO — systém dokáže aplikovať automaticky (napr. zmena sadzby)
   - REVIEW — vyžaduje ľudskú verifikáciu (napr. nový riadok výkazu)
   - MANUAL — vyžaduje manuálnu implementáciu (napr. úplne nový výkaz)

### 13.5 Vrstva 3 — Adaptive Configuration

Versionované konfigurácie: Všetky legislatívne závislé konfigurácie sú verzionované s platnosťou (valid_from, valid_to):

```
legislative_config
├── id (PK)
├── config_type (tax_rate | report_mapping | chart_template | xsd_schema)
├── config_key (napr. 'corporate_tax_rate', 'balance_sheet_v2025')
├── config_value (JSONB)
├── valid_from (DATE)
├── valid_to (DATE, nullable)
├── source_law (napr. '595/2003 Z.z. §15')
├── created_at
├── auto_applied (BOOLEAN)
└── approved_by (nullable — pre REVIEW items)
```

**Príklady auto-adaptácie:**
- Sadzba dane z príjmov PO: zmena z 21% na 22% → nový záznam s valid_from = 2026-01-01
- XSD schéma DPH priznania: nová verzia → automatický download + validácia kompatibility
- Vzor Súvahy: nový riadok → AI navrhne mapovanie, čaká na schválenie

Bezpečnostný princíp: AUTO zmeny sa aplikujú okamžite, ale VŽDY s notifikáciou. REVIEW a MANUAL zmeny NIKDY bez explicitného schválenia.

### 13.6 XSD Schema Registry

Účel: Centrálna správa XML schém Finančnej správy.

```
xsd_registry
├── id (PK)
├── schema_type (vat_return | vat_control | income_tax | balance_sheet | ...)
├── version
├── xsd_content (TEXT)
├── xsd_hash (SHA-256)
├── downloaded_from (URL)
├── downloaded_at
├── valid_from
├── is_active (BOOLEAN)
└── previous_version_id (FK → self)
```

- Automatický download nových XSD z financnasprava.sk
- Diff analýza oproti predchádzajúcej verzii
- Automatický test: existujúce XML výstupy validovať proti novej XSD
- Ak validácia zlyhá → REVIEW alert

### 13.7 Notifikačný systém

Pri každej legislatívnej zmene:
1. Dashboard widget — "Legislatívne zmeny" panel s farebnými indikátormi
2. Email notifikácia — na director účet
3. Compliance status per tenant — zelená/žltá/červená:
   - Zelená: všetky konfigurácie aktuálne
   - Žltá: REVIEW items čakajú na schválenie
   - Červená: MANUAL zmena potrebná, systém môže generovať neplatné výkazy

## 14. OTVORENÉ OTÁZKY

1. **FS API:** Overiť dostupnosť a dokumentáciu API portálu FS pre elektronické podanie (SOAP vs REST vs Playwright automatizácia) — riešiť v Phase 3 (v1.0.0) resp. Phase 4 (v2.0.0).

## 15. KNOWN TECHNICAL CONSTRAINTS

### Alembic + SQLAlchemy ENUM Migration Pattern (MANDATORY)

When creating Alembic migrations with PostgreSQL ENUM types, **NEVER** use `sa.Enum()` in `op.create_table()`. SQLAlchemy ignores `create_type=False` when the same named ENUM is registered in `Base.metadata` via model imports in `env.py`, causing "type already exists" errors.

**Correct pattern:**
1. Create ENUM types with raw SQL: `op.execute("CREATE TYPE IF NOT EXISTS enum_name AS ENUM ('val1', 'val2')")`
2. Reference in `op.create_table()` with: `postgresql.ENUM('val1', 'val2', name='enum_name', create_type=False)`
3. Drop in downgrade with: `op.execute("DROP TYPE IF EXISTS enum_name")`

**Wrong pattern (DO NOT USE):**
- `sa.Enum('val1', 'val2', name='enum_name', create_type=False)` — ignores `create_type=False`
- `sa.Enum(MyPythonEnum, name='enum_name')` — auto-creates type, conflicts with env.py imports

### PostgreSQL Healthcheck Pattern

`pg_isready -U <user>` bez `-d` parametra sa pokúša pripojiť na DB s názvom usera. Ak DB `<user>` neexistuje, generuje `FATAL: database "<user>" does not exist` každých N sekúnd.

**Correct:** `pg_isready -U ledger -d nex_ledger`
**Wrong:** `pg_isready -U ledger` (defaultuje na DB `ledger`)

### Python 3.12 Datetime

`datetime.utcnow()` je **DEPRECATED** od Python 3.12 (DeprecationWarning).

Pre SQLAlchemy timestamp columns:
- **Server-side (preferované):** `server_default=func.now()`, `onupdate=func.now()`
- **Python-side ak nutné:** `datetime.now(datetime.UTC)`
- **NIKDY:** `datetime.utcnow`

### UniqueConstraint vs Column unique

**NIKDY** nepoužívať oboje `Column(..., unique=True)` + `UniqueConstraint("col")` na rovnaký stĺpec — vytvorí dva identické unique indexy v DB.

- `unique=True` na `Column` — pre single-column unique constraint
- `UniqueConstraint("col1", "col2")` v `__table_args__` — pre multi-column composite unique

### Test Fixtures — DRY

Shared fixtures (napr. `db_session`) **MUSIA** byť v `tests/conftest.py`. NIKDY copy-paste rovnakej fixture do viacerých test súborov.

### server_default Konzistencia

Ak Boolean column má `default=False`, **MUSÍ** mať aj `server_default="false"`. Raw SQL inserts a Alembic data migrácie nepoužívajú Python defaults.

**Correct:** `Column(Boolean, default=False, nullable=False, server_default="false")`
**Wrong:** `Column(Boolean, default=False, nullable=False)` — raw SQL insert bez `is_system` zlyhá alebo použije NULL

### Alembic Autogenerate Lint (MANDATORY)

`alembic revision --autogenerate` generuje legacy syntax `Union[str, Sequence[str], None]` namiesto Python 3.12 union syntax `str | Sequence[str] | None`. Ruff pravidlo **UP007** toto zachytí ako error.

**POVINNÉ:** Po každom `alembic revision --autogenerate` VŽDY spustiť `ruff check --fix` na vygenerovaný súbor pred commitom.

**Pattern:**
```bash
alembic revision --autogenerate -m "description" && ruff check --fix alembic/versions/
```

### Test DB Isolation (CRITICAL)

Testy **NIKDY** nesmú používať produkčný `DATABASE_URL`. `conftest.py` **MUSÍ** použiť `TEST_DATABASE_URL` env var.

**Pravidlá:**
1. Test DB = oddelená databáza (napr. `nex_ledger_test`) vedľa produkčnej
2. `Base.metadata.drop_all()` len na test DB — **NIKDY** na produkčný
3. `docker-compose.yml` musí obsahovať init script na vytvorenie test DB
4. CI: `DATABASE_URL` aj `TEST_DATABASE_URL` musia ukazovať na oddelené DB

**ROOT CAUSE:** Audit #2 odhalil, že `drop_all()` v `conftest.py` zničila všetkých 5 produkčných tabuliek. `alembic_version` zostala (nie je v `Base.metadata`), ale domény tabuľky zmizli. Alembic ukazoval "head" ale DB bola prázdna.

**Correct pattern:**
```python
# conftest.py
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+pg8000://ledger:ledger@localhost:9181/nex_ledger_test")
engine = create_engine(TEST_DB_URL)
```

**Wrong pattern (DO NOT USE):**
```python
# conftest.py — ZNIČÍ produkčné tabuľky!
from app.database import settings
engine = create_engine(settings.database_url)  # ← produkčný DB
```

### Model Generation Konzistencia

Všetky modely v projekte **MUSIA** dodržiavať rovnaký vzor. Nekonzistentnosť medzi modelmi je audit WARN.

**Pravidlá:**
1. UniqueConstraint: vždy v `__table_args__` s explicitným `name=`, **nikdy** `unique=True` na Column
   - Formát: `name="uq_{table}_{column}"` (napr. `uq_currency_code`)
2. Boolean columns: vždy `server_default` (napr. `server_default="false"`)
3. Integer columns s `default`: vždy aj `server_default` (napr. `server_default="0"`)
4. Žiadne `index=True` ak je `unique=True` (unique implikuje index → duplikátny index)
5. Všetky `UniqueConstraint` musia mať explicitný `name=` parameter

**ROOT CAUSE:** Audit #2 odhalil nekonzistentnosť medzi 5 modelmi — AccountType bol opravený v audite #1 (UniqueConstraint v `__table_args__`), ale Currency, TaxRate, BusinessPartner a ImportBatch stále používali `unique=True` na Column. ImportBatch navyše mal `unique=True` + `index=True` (duplikátny index).

### pg8000 + postgresql.ENUM values_callable (MANDATORY)

pg8000 driver (na rozdiel od psycopg2) **nevie** automaticky mapovať Python `StrEnum` na PostgreSQL ENUM values. Bez `values_callable` parameter SQLAlchemy posiela Python enum objekt namiesto stringu, čo spôsobí runtime error.

**Correct pattern:**
```python
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

class MyStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

status = Column(
    PG_ENUM(MyStatus, name="my_status_enum", create_type=False,
            values_callable=lambda e: [m.value for m in e]),
    nullable=False,
)
```

**Wrong pattern (DO NOT USE with pg8000):**
```python
# Bez values_callable — pg8000 pošle <MyStatus.ACTIVE: 'active'> namiesto 'active'
status = Column(PG_ENUM(MyStatus, name="my_status_enum", create_type=False))
```

**ROOT CAUSE:** AccountType model používal `PG_ENUM` bez `values_callable`. S pg8000 driverom INSERT zlyhal na type mismatch. Opravené pridaním `values_callable=lambda e: [m.value for m in e]` na všetky `PG_ENUM` columns.