"""Tests for JournalEntryLine model."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.business_partner import BusinessPartner
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.models.tax_rate import TaxRate


def _create_full_dependencies(db_session):
    """Create all FK dependencies needed for JournalEntryLine tests.

    Returns:
        tuple: (entry, account_cash, account_revenue, currency, partner, tax_rate)
    """
    # Currency
    currency = Currency(currency_code="EUR", name="Euro")
    db_session.add(currency)
    db_session.flush()

    # AccountType
    account_type = AccountType(code="ASSET", name="Assets")
    db_session.add(account_type)
    db_session.flush()

    # ChartOfAccounts
    chart = ChartOfAccounts(code="SK2025", name="Test Chart")
    db_session.add(chart)
    db_session.flush()

    # Two accounts — one for debit, one for credit
    account_cash = Account(
        chart_id=chart.chart_id,
        account_number="211000",
        name="Pokladnica",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account_cash)
    db_session.flush()

    revenue_type = AccountType(code="REVENUE", name="Revenue")
    db_session.add(revenue_type)
    db_session.flush()

    account_revenue = Account(
        chart_id=chart.chart_id,
        account_number="601000",
        name="Tržby za vlastné výrobky",
        account_type_id=revenue_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account_revenue)
    db_session.flush()

    # BusinessPartner
    partner = BusinessPartner(
        partner_type="CUSTOMER",
        code="CUST-001",
        name="Test Partner s.r.o.",
    )
    db_session.add(partner)
    db_session.flush()

    # TaxRate
    tax_rate = TaxRate(
        code="VAT20",
        name="DPH 20%",
        rate=Decimal("20.00"),
    )
    db_session.add(tax_rate)
    db_session.flush()

    # JournalEntry
    entry = JournalEntry(
        entry_number="JEL-TEST-001",
        entry_date=date(2026, 3, 28),
        description="Test entry for lines",
    )
    db_session.add(entry)
    db_session.flush()

    return entry, account_cash, account_revenue, currency, partner, tax_rate


# ── Test 1: Create lines (debit + credit) ──────────────────────────


def test_create_lines(db_session):
    """Test creating JournalEntry with 2 JournalEntryLine records (debit + credit)."""
    entry, account_cash, account_revenue, currency, partner, tax_rate = (
        _create_full_dependencies(db_session)
    )

    # Debit line: account 211000 (Pokladnica)
    line_debit = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        partner_id=partner.partner_id,
        tax_rate_id=tax_rate.tax_rate_id,
        debit_amount=Decimal("1500.00"),
        credit_amount=Decimal("0.00"),
        description="Príjem do pokladne",
        currency_code=currency.currency_code,
    )

    # Credit line: account 601000 (Tržby)
    line_credit = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=2,
        account_id=account_revenue.account_id,
        partner_id=partner.partner_id,
        tax_rate_id=tax_rate.tax_rate_id,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("1500.00"),
        description="Tržba za výrobky",
        currency_code=currency.currency_code,
    )

    db_session.add_all([line_debit, line_credit])
    db_session.commit()

    # Verify both lines inserted
    assert line_debit.line_id is not None
    assert line_credit.line_id is not None
    assert line_debit.entry_id == entry.entry_id
    assert line_credit.entry_id == entry.entry_id
    assert line_debit.line_number == 1
    assert line_credit.line_number == 2
    assert line_debit.debit_amount == Decimal("1500.00")
    assert line_debit.credit_amount == Decimal("0.00")
    assert line_credit.debit_amount == Decimal("0.00")
    assert line_credit.credit_amount == Decimal("1500.00")
    assert line_debit.partner_id == partner.partner_id
    assert line_debit.tax_rate_id == tax_rate.tax_rate_id
    assert line_debit.currency_code == "EUR"

    # Verify count via query
    count = (
        db_session.query(JournalEntryLine)
        .filter_by(entry_id=entry.entry_id)
        .count()
    )
    assert count == 2


# ── Test 2: Unique constraint (entry_id, line_number) ──────────────


def test_unique_constraint(db_session):
    """Test UNIQUE constraint on (entry_id, line_number) — duplicate must fail."""
    entry, account_cash, account_revenue, currency, partner, tax_rate = (
        _create_full_dependencies(db_session)
    )

    line1 = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        debit_amount=Decimal("100.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line1)
    db_session.commit()

    # Duplicate: same entry_id + line_number
    line2 = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_revenue.account_id,
        credit_amount=Decimal("100.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


# ── Test 3: FK constraints (all 5) ─────────────────────────────────


def test_fk_cascade_journal_entry_delete(db_session):
    """Test CASCADE: deleting journal_entry must delete its lines."""
    entry, account_cash, _, currency, _, _ = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        debit_amount=Decimal("500.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()
    line_id = line.line_id

    # Delete journal_entry via raw SQL → line should be CASCADE-deleted
    db_session.execute(
        text("DELETE FROM journal_entry WHERE entry_id = :id"),
        {"id": entry.entry_id},
    )
    db_session.commit()

    deleted = db_session.get(JournalEntryLine, line_id)
    assert deleted is None


def test_fk_restrict_account_delete(db_session):
    """Test RESTRICT: deleting account referenced by line must fail."""
    entry, account_cash, _, currency, _, _ = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        debit_amount=Decimal("500.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()

    # RESTRICT: delete account must fail
    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text("DELETE FROM account WHERE account_id = :id"),
            {"id": account_cash.account_id},
        )
        db_session.flush()


def test_fk_set_null_partner_delete(db_session):
    """Test SET NULL: deleting business_partner sets partner_id to NULL."""
    entry, account_cash, _, currency, partner, _ = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        partner_id=partner.partner_id,
        debit_amount=Decimal("500.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()
    line_id = line.line_id

    # Delete partner → partner_id should become NULL
    db_session.execute(
        text("DELETE FROM business_partner WHERE partner_id = :id"),
        {"id": partner.partner_id},
    )
    db_session.commit()

    db_session.expire_all()
    reloaded = db_session.get(JournalEntryLine, line_id)
    assert reloaded is not None
    assert reloaded.partner_id is None


def test_fk_set_null_tax_rate_delete(db_session):
    """Test SET NULL: deleting tax_rate sets tax_rate_id to NULL."""
    entry, account_cash, _, currency, _, tax_rate = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        tax_rate_id=tax_rate.tax_rate_id,
        debit_amount=Decimal("500.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()
    line_id = line.line_id

    # Delete tax_rate → tax_rate_id should become NULL
    db_session.execute(
        text("DELETE FROM tax_rate WHERE tax_rate_id = :id"),
        {"id": tax_rate.tax_rate_id},
    )
    db_session.commit()

    db_session.expire_all()
    reloaded = db_session.get(JournalEntryLine, line_id)
    assert reloaded is not None
    assert reloaded.tax_rate_id is None


def test_fk_restrict_currency_delete(db_session):
    """Test RESTRICT: deleting currency referenced by line must fail."""
    entry, account_cash, _, currency, _, _ = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        debit_amount=Decimal("500.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()

    # RESTRICT: delete currency must fail (also used by account, but testing line FK)
    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text("DELETE FROM currency WHERE currency_code = :code"),
            {"code": currency.currency_code},
        )
        db_session.flush()


# ── Bonus: server defaults and repr ────────────────────────────────


def test_server_defaults(db_session):
    """Test server_default values for debit/credit amounts."""
    entry, account_cash, _, currency, _, _ = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()

    db_session.refresh(line)
    assert line.debit_amount == Decimal("0")
    assert line.credit_amount == Decimal("0")


def test_repr(db_session):
    """Test __repr__ output."""
    entry, account_cash, _, currency, _, _ = _create_full_dependencies(db_session)

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account_cash.account_id,
        debit_amount=Decimal("100.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(line)
    db_session.commit()

    repr_str = repr(line)
    assert "JournalEntryLine" in repr_str
    assert f"line_id={line.line_id}" in repr_str
    assert f"entry_id={entry.entry_id}" in repr_str
    assert "line_number=1" in repr_str
