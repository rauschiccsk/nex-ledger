"""Tests for JournalLine model."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.models import (
    Account,
    AccountCategory,
    AccountType,
    BusinessPartner,
    Currency,
    JournalEntry,
    JournalLine,
    NormalBalance,
    TaxRate,
)

# ---------------------------------------------------------------------------
# Helpers — common prerequisite objects
# ---------------------------------------------------------------------------


def _make_prerequisites(db_session):
    """Create and commit common prerequisite objects for journal line tests."""
    account_type = AccountType(
        code="BANK",
        name="Bank Account",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    currency = Currency(code="EUR", name="Euro", symbol="€", decimal_places=2)
    db_session.add_all([account_type, currency])
    db_session.flush()

    account = Account(
        code="1010",
        name="Bank Account",
        account_type=account_type,
        currency=currency,
    )
    db_session.add(account)
    db_session.flush()

    entry = JournalEntry(
        entry_number="JE001",
        entry_date=date(2024, 1, 1),
        description="Test entry",
    )
    db_session.add(entry)
    db_session.commit()

    return account_type, currency, account, entry


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_journal_line_create(db_session):
    """Test creating a journal line with all fields."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    partner = BusinessPartner(
        code="CUST001", name="Test Customer", is_customer=True
    )
    tax_rate = TaxRate(
        code="VAT20",
        name="VAT 20%",
        rate_percent=Decimal("20.00"),
        valid_from=date(2024, 1, 1),
    )
    db_session.add_all([partner, tax_rate])
    db_session.commit()

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("1000.00"),
        credit_amount=Decimal("0.00"),
        description="Test debit",
        business_partner=partner,
        tax_rate=tax_rate,
        tax_base_amount=Decimal("833.33"),
        tax_amount=Decimal("166.67"),
    )
    db_session.add(line)
    db_session.commit()

    assert line.id is not None
    assert line.journal_entry_id == entry.id
    assert line.line_number == 1
    assert line.debit_amount == Decimal("1000.00")
    assert line.credit_amount == Decimal("0.00")
    assert line.description == "Test debit"
    assert line.business_partner_id == partner.id
    assert line.tax_rate_id == tax_rate.id
    assert line.tax_base_amount == Decimal("833.33")
    assert line.tax_amount == Decimal("166.67")
    assert line.created_at is not None
    assert line.updated_at is not None


def test_journal_line_unique_entry_line(db_session):
    """Test UNIQUE constraint on (journal_entry_id, line_number)."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line1 = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("100.00"),
    )
    db_session.add(line1)
    db_session.commit()

    line2 = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("200.00"),
    )
    db_session.add(line2)

    with pytest.raises(Exception):  # IntegrityError or ProgrammingError (pg8000)
        db_session.commit()


def test_journal_line_debit_negative_rejected(db_session):
    """Test CHECK constraint: debit_amount >= 0."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("-100.00"),
    )
    db_session.add(line)

    with pytest.raises(Exception):  # CheckViolation
        db_session.commit()


def test_journal_line_credit_negative_rejected(db_session):
    """Test CHECK constraint: credit_amount >= 0."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        credit_amount=Decimal("-50.00"),
    )
    db_session.add(line)

    with pytest.raises(Exception):  # CheckViolation
        db_session.commit()


def test_journal_line_both_debit_and_credit_rejected(db_session):
    """Test CHECK constraint: NOT (debit > 0 AND credit > 0)."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("50.00"),  # Both > 0 — forbidden
    )
    db_session.add(line)

    with pytest.raises(Exception):  # CheckViolation
        db_session.commit()


def test_journal_line_cascade_delete(db_session):
    """Test CASCADE delete when journal_entry is deleted."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("100.00"),
    )
    db_session.add(line)
    db_session.commit()

    line_id = line.id

    # Delete entry — lines should cascade
    db_session.delete(entry)
    db_session.commit()

    assert db_session.get(JournalLine, line_id) is None


def test_journal_line_account_restrict(db_session):
    """Test RESTRICT delete on account FK — raw SQL per pg8000 FK pattern."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("100.00"),
    )
    db_session.add(line)
    db_session.commit()

    # pg8000 maps FK violation 23503 to ProgrammingError, not IntegrityError
    from sqlalchemy.exc import IntegrityError, ProgrammingError

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text("DELETE FROM account WHERE id = :id"),
            {"id": account.id},
        )
        db_session.flush()


def test_journal_line_repr(db_session):
    """Test __repr__ method."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("100.00"),
    )
    db_session.add(line)
    db_session.commit()

    repr_str = repr(line)
    assert "JournalLine" in repr_str
    assert str(entry.id) in repr_str
    assert "line=1" in repr_str


def test_journal_line_relationships_bidirectional(db_session):
    """Test bidirectional relationships — entry.lines, account.journal_lines, etc."""
    _at, _cur, account, entry = _make_prerequisites(db_session)

    partner = BusinessPartner(
        code="SUP001", name="Supplier One", is_supplier=True
    )
    tax_rate = TaxRate(
        code="VAT10",
        name="VAT 10%",
        rate_percent=Decimal("10.00"),
        valid_from=date(2024, 1, 1),
    )
    db_session.add_all([partner, tax_rate])
    db_session.commit()

    line = JournalLine(
        journal_entry=entry,
        line_number=1,
        account=account,
        debit_amount=Decimal("500.00"),
        business_partner=partner,
        tax_rate=tax_rate,
    )
    db_session.add(line)
    db_session.commit()

    # Bidirectional checks
    assert line in entry.lines
    assert line in account.journal_lines
    assert line in partner.journal_lines
    assert line in tax_rate.journal_lines
