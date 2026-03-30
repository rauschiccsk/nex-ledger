"""
Tests for CurrencyService CRUD operations.

Covers: list_currencies, get_currency, create_currency, update_currency, delete_currency.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.import_batch import ImportBatch
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.services.currency_service import CurrencyService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def eur(db_session: Session) -> Currency:
    """Create EUR currency."""
    cur = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(cur)
    db_session.flush()
    return cur


@pytest.fixture()
def usd(db_session: Session) -> Currency:
    """Create USD currency."""
    cur = Currency(currency_code="USD", name="US Dollar", symbol="$")
    db_session.add(cur)
    db_session.flush()
    return cur


@pytest.fixture()
def multiple_currencies(db_session: Session) -> list[Currency]:
    """Create 5 currencies for pagination testing."""
    codes = [
        ("CZK", "Czech Koruna", "Kč"),
        ("EUR", "Euro", "€"),
        ("GBP", "British Pound", "£"),
        ("JPY", "Japanese Yen", "¥"),
        ("USD", "US Dollar", "$"),
    ]
    currencies = []
    for code, name, symbol in codes:
        cur = Currency(currency_code=code, name=name, symbol=symbol)
        db_session.add(cur)
        db_session.flush()
        currencies.append(cur)
    return currencies


@pytest.fixture()
def journal_entry_with_currency(
    db_session: Session, eur: Currency
) -> JournalEntryLine:
    """Create journal entry infrastructure referencing EUR currency."""
    # AccountType
    at = AccountType(code="ASSET", name="Assets")
    db_session.add(at)
    db_session.flush()

    # ChartOfAccounts
    coa = ChartOfAccounts(code="SK-2025", name="Slovak Chart 2025")
    db_session.add(coa)
    db_session.flush()

    # Account
    account = Account(
        chart_id=coa.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=at.account_type_id,
        currency_code=eur.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.flush()

    # ImportBatch
    batch = ImportBatch(
        filename="test.csv",
        file_hash="a" * 64,
        status="imported",
    )
    db_session.add(batch)
    db_session.flush()

    # JournalEntry
    entry = JournalEntry(
        batch_id=batch.batch_id,
        entry_number="JE-001",
        entry_date=date(2025, 1, 1),
        description="Test entry",
    )
    db_session.add(entry)
    db_session.flush()

    # JournalEntryLine with EUR
    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account.account_id,
        debit_amount=Decimal("1000.00"),
        credit_amount=Decimal("0.00"),
        currency_code=eur.currency_code,
    )
    db_session.add(line)
    db_session.flush()

    return line


# ── list_currencies Tests ────────────────────────────────────────


class TestListCurrencies:
    """Tests for CurrencyService.list_currencies()."""

    def test_list_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        currencies, total = CurrencyService.list_currencies(db_session)

        assert currencies == []
        assert total == 0

    def test_list_pagination(
        self, db_session: Session, multiple_currencies: list[Currency]
    ):
        """Skip/limit pagination returns correct subset."""
        currencies, total = CurrencyService.list_currencies(
            db_session, skip=1, limit=2
        )

        assert len(currencies) == 2
        assert total == 5

    def test_list_ordering(
        self, db_session: Session, multiple_currencies: list[Currency]
    ):
        """Currencies are ordered by currency_code ASC."""
        currencies, total = CurrencyService.list_currencies(db_session)

        assert total == 5
        assert len(currencies) == 5

        codes = [c.currency_code for c in currencies]
        assert codes == sorted(codes)
        assert codes == ["CZK", "EUR", "GBP", "JPY", "USD"]


# ── get_currency Tests ───────────────────────────────────────────


class TestGetCurrency:
    """Tests for CurrencyService.get_currency()."""

    def test_get_success(self, db_session: Session, eur: Currency):
        """Existing currency is returned correctly."""
        result = CurrencyService.get_currency(db_session, "EUR")

        assert result.currency_code == "EUR"
        assert result.name == "Euro"
        assert result.symbol == "€"

    def test_get_not_found(self, db_session: Session):
        """Non-existent currency raises ValueError."""
        with pytest.raises(ValueError, match="Currency not found: XXX"):
            CurrencyService.get_currency(db_session, "XXX")


# ── create_currency Tests ────────────────────────────────────────


class TestCreateCurrency:
    """Tests for CurrencyService.create_currency()."""

    def test_create_success(self, db_session: Session):
        """Currency is created with required fields."""
        currency = CurrencyService.create_currency(
            db_session,
            {"currency_code": "USD", "name": "US Dollar", "symbol": "$"},
        )

        assert currency.currency_code == "USD"
        assert currency.name == "US Dollar"
        assert currency.symbol == "$"

        # Verify in DB
        result = db_session.execute(
            select(Currency).where(Currency.currency_code == "USD")
        ).scalar_one_or_none()
        assert result is not None
        assert result.name == "US Dollar"

    def test_create_duplicate(self, db_session: Session, eur: Currency):
        """Duplicate currency_code raises ValueError."""
        with pytest.raises(ValueError, match="Currency already exists: EUR"):
            CurrencyService.create_currency(
                db_session,
                {"currency_code": "EUR", "name": "Euro Duplicate"},
            )

    def test_create_invalid_code_short(self, db_session: Session):
        """Currency code with wrong length raises ValueError."""
        with pytest.raises(ValueError, match="Currency code must be 3 characters"):
            CurrencyService.create_currency(
                db_session,
                {"currency_code": "EU", "name": "Invalid"},
            )

    def test_create_invalid_code_empty(self, db_session: Session):
        """Empty currency code raises ValueError."""
        with pytest.raises(ValueError, match="Currency code must be 3 characters"):
            CurrencyService.create_currency(
                db_session,
                {"currency_code": "", "name": "Invalid"},
            )

    def test_create_missing_name(self, db_session: Session):
        """Missing name raises ValueError."""
        with pytest.raises(ValueError, match="Currency name is required"):
            CurrencyService.create_currency(
                db_session,
                {"currency_code": "USD"},
            )

    def test_create_uppercase_normalization(self, db_session: Session):
        """Lowercase code is normalized to uppercase."""
        currency = CurrencyService.create_currency(
            db_session,
            {"currency_code": "gbp", "name": "British Pound", "symbol": "£"},
        )

        assert currency.currency_code == "GBP"


# ── update_currency Tests ────────────────────────────────────────


class TestUpdateCurrency:
    """Tests for CurrencyService.update_currency()."""

    def test_update_name(self, db_session: Session, eur: Currency):
        """Currency name can be updated."""
        updated = CurrencyService.update_currency(
            db_session, "EUR", {"name": "Euro (updated)"}
        )

        assert updated.name == "Euro (updated)"
        assert updated.currency_code == "EUR"

    def test_update_symbol(self, db_session: Session, eur: Currency):
        """Currency symbol can be updated."""
        updated = CurrencyService.update_currency(
            db_session, "EUR", {"symbol": "EUR€"}
        )

        assert updated.symbol == "EUR€"

    def test_update_immutable_pk(self, db_session: Session, eur: Currency):
        """Attempt to update currency_code is silently ignored."""
        updated = CurrencyService.update_currency(
            db_session,
            "EUR",
            {"currency_code": "XXX", "name": "Still Euro"},
        )

        # PK must remain EUR
        assert updated.currency_code == "EUR"
        assert updated.name == "Still Euro"

    def test_update_not_found(self, db_session: Session):
        """Non-existent currency raises ValueError."""
        with pytest.raises(ValueError, match="Currency not found: XXX"):
            CurrencyService.update_currency(
                db_session, "XXX", {"name": "Ghost"}
            )


# ── delete_currency Tests ────────────────────────────────────────


class TestDeleteCurrency:
    """Tests for CurrencyService.delete_currency()."""

    def test_delete_success(self, db_session: Session, eur: Currency):
        """Unused currency is deleted successfully."""
        CurrencyService.delete_currency(db_session, "EUR")

        # Verify currency no longer exists
        result = db_session.execute(
            select(Currency).where(Currency.currency_code == "EUR")
        ).scalar_one_or_none()
        assert result is None

    def test_delete_in_use(
        self,
        db_session: Session,
        eur: Currency,
        journal_entry_with_currency: JournalEntryLine,
    ):
        """Currency referenced by journal_entry_line cannot be deleted."""
        with pytest.raises(
            ValueError, match="Cannot delete currency EUR: in use"
        ):
            CurrencyService.delete_currency(db_session, "EUR")

    def test_delete_not_found(self, db_session: Session):
        """Non-existent currency raises ValueError."""
        with pytest.raises(ValueError, match="Currency not found: XXX"):
            CurrencyService.delete_currency(db_session, "XXX")
