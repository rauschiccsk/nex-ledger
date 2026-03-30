"""
Tests for TaxRateService CRUD operations.

Covers: list_tax_rates, get_tax_rate, create_tax_rate,
        update_tax_rate, delete_tax_rate.
"""

import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.models.tax_rate import TaxRate
from app.services.tax_rate_service import TaxRateService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def vat20(db_session: Session) -> TaxRate:
    """Create a 20% VAT tax rate."""
    tr = TaxRate(code="VAT20", name="VAT 20%", rate=Decimal("20.00"))
    db_session.add(tr)
    db_session.flush()
    return tr


@pytest.fixture()
def vat10(db_session: Session) -> TaxRate:
    """Create a 10% VAT tax rate."""
    tr = TaxRate(code="VAT10", name="VAT 10%", rate=Decimal("10.00"))
    db_session.add(tr)
    db_session.flush()
    return tr


@pytest.fixture()
def multiple_tax_rates(db_session: Session) -> list[TaxRate]:
    """Create 5 tax rates for pagination testing."""
    rates_data = [
        ("VAT20", "VAT 20%", Decimal("20.00")),
        ("VAT10", "VAT 10%", Decimal("10.00")),
        ("VAT0", "VAT 0%", Decimal("0.00")),
        ("ST5", "Sales Tax 5%", Decimal("5.00")),
        ("ST15", "Sales Tax 15%", Decimal("15.00")),
    ]
    tax_rates = []
    for code, name, rate in rates_data:
        tr = TaxRate(code=code, name=name, rate=rate)
        db_session.add(tr)
        db_session.flush()
        tax_rates.append(tr)
    return tax_rates


@pytest.fixture()
def tax_rate_with_journal_line(
    db_session: Session, vat20: TaxRate
) -> JournalEntryLine:
    """Create a journal entry line referencing the VAT20 tax rate."""
    # Currency
    cur = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(cur)
    db_session.flush()

    # ChartOfAccounts
    coa = ChartOfAccounts(code="SK-2025", name="Slovak Chart 2025")
    db_session.add(coa)
    db_session.flush()

    # AccountType
    at = AccountType(code="ASSET", name="Assets")
    db_session.add(at)
    db_session.flush()

    # Account
    account = Account(
        chart_id=coa.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=at.account_type_id,
        currency_code=cur.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.flush()

    # JournalEntry
    entry = JournalEntry(
        entry_number="JE-001",
        entry_date=datetime.date(2025, 1, 15),
        description="Test entry",
    )
    db_session.add(entry)
    db_session.flush()

    # JournalEntryLine referencing vat20
    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account.account_id,
        tax_rate_id=vat20.tax_rate_id,
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("0.00"),
        currency_code=cur.currency_code,
    )
    db_session.add(line)
    db_session.flush()
    return line


# ── list_tax_rates Tests ─────────────────────────────────────────


class TestListTaxRates:
    """Tests for TaxRateService.list_tax_rates()."""

    def test_list_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        tax_rates, total = TaxRateService.list_tax_rates(db_session)

        assert tax_rates == []
        assert total == 0

    def test_list_with_pagination(
        self, db_session: Session, multiple_tax_rates: list[TaxRate]
    ):
        """Skip/limit pagination returns correct subset."""
        tax_rates, total = TaxRateService.list_tax_rates(
            db_session, skip=2, limit=2
        )

        assert len(tax_rates) == 2
        assert total == 5

        # IDs are autoincrement — skip=2 returns 3rd and 4th inserted
        ids = [tr.tax_rate_id for tr in tax_rates]
        expected_ids = [
            multiple_tax_rates[2].tax_rate_id,
            multiple_tax_rates[3].tax_rate_id,
        ]
        assert ids == expected_ids

    def test_list_ordering(
        self, db_session: Session, multiple_tax_rates: list[TaxRate]
    ):
        """Tax rates are ordered by tax_rate_id ASC."""
        tax_rates, total = TaxRateService.list_tax_rates(db_session)

        assert total == 5
        assert len(tax_rates) == 5

        ids = [tr.tax_rate_id for tr in tax_rates]
        assert ids == sorted(ids)


# ── get_tax_rate Tests ───────────────────────────────────────────


class TestGetTaxRate:
    """Tests for TaxRateService.get_tax_rate()."""

    def test_get_success(self, db_session: Session, vat20: TaxRate):
        """Existing tax rate is returned correctly."""
        result = TaxRateService.get_tax_rate(
            db_session, vat20.tax_rate_id
        )

        assert result.tax_rate_id == vat20.tax_rate_id
        assert result.code == "VAT20"
        assert result.name == "VAT 20%"
        assert result.rate == Decimal("20.00")

    def test_get_not_found(self, db_session: Session):
        """Non-existent tax rate raises ValueError."""
        with pytest.raises(ValueError, match="TaxRate 99999 not found"):
            TaxRateService.get_tax_rate(db_session, 99999)


# ── create_tax_rate Tests ────────────────────────────────────────


class TestCreateTaxRate:
    """Tests for TaxRateService.create_tax_rate()."""

    def test_create_success(self, db_session: Session):
        """Tax rate is created with required fields."""
        tax_rate = TaxRateService.create_tax_rate(
            db_session,
            {
                "code": "VAT20",
                "name": "VAT 20%",
                "rate": Decimal("20.00"),
            },
        )

        assert tax_rate.code == "VAT20"
        assert tax_rate.name == "VAT 20%"
        assert tax_rate.rate == Decimal("20.00")
        assert tax_rate.tax_rate_id is not None

        # Verify in DB
        result = db_session.execute(
            select(TaxRate).where(
                TaxRate.tax_rate_id == tax_rate.tax_rate_id
            )
        ).scalar_one_or_none()
        assert result is not None
        assert result.name == "VAT 20%"

    def test_create_missing_name(self, db_session: Session):
        """Missing name raises ValueError."""
        with pytest.raises(ValueError, match="Tax rate name is required"):
            TaxRateService.create_tax_rate(
                db_session,
                {"code": "VAT20", "rate": Decimal("20.00")},
            )

    def test_create_missing_rate(self, db_session: Session):
        """Missing rate raises ValueError."""
        with pytest.raises(ValueError, match="Tax rate rate is required"):
            TaxRateService.create_tax_rate(
                db_session,
                {"code": "VAT20", "name": "VAT 20%"},
            )


# ── update_tax_rate Tests ────────────────────────────────────────


class TestUpdateTaxRate:
    """Tests for TaxRateService.update_tax_rate()."""

    def test_update_success(self, db_session: Session, vat20: TaxRate):
        """Tax rate name and rate can be updated."""
        updated = TaxRateService.update_tax_rate(
            db_session,
            vat20.tax_rate_id,
            {"name": "Updated VAT", "rate": Decimal("21.00")},
        )

        assert updated.name == "Updated VAT"
        assert updated.rate == Decimal("21.00")
        assert updated.code == "VAT20"

    def test_update_not_found(self, db_session: Session):
        """Non-existent tax rate raises ValueError."""
        with pytest.raises(ValueError, match="TaxRate 99999 not found"):
            TaxRateService.update_tax_rate(
                db_session, 99999, {"name": "Ghost"}
            )


# ── delete_tax_rate Tests ────────────────────────────────────────


class TestDeleteTaxRate:
    """Tests for TaxRateService.delete_tax_rate()."""

    def test_delete_success(self, db_session: Session, vat20: TaxRate):
        """Unused tax rate is deleted successfully."""
        rate_id = vat20.tax_rate_id
        TaxRateService.delete_tax_rate(db_session, rate_id)

        # Verify tax rate no longer exists
        result = db_session.execute(
            select(TaxRate).where(TaxRate.tax_rate_id == rate_id)
        ).scalar_one_or_none()
        assert result is None

    def test_delete_has_journal_entries(
        self,
        db_session: Session,
        vat20: TaxRate,
        tax_rate_with_journal_line: JournalEntryLine,
    ):
        """Tax rate referenced by journal entry lines cannot be deleted."""
        with pytest.raises(
            ValueError,
            match="Cannot delete tax_rate with journal entries",
        ):
            TaxRateService.delete_tax_rate(
                db_session, vat20.tax_rate_id
            )

    def test_delete_not_found(self, db_session: Session):
        """Non-existent tax rate raises ValueError."""
        with pytest.raises(ValueError, match="TaxRate 99999 not found"):
            TaxRateService.delete_tax_rate(db_session, 99999)
