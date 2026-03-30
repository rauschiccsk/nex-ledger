"""Unit testy pre JournalEntry a JournalEntryLine Pydantic schemas."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryLineCreate,
    JournalEntryLineRead,
    JournalEntryLineUpdate,
    JournalEntryRead,
    JournalEntryUpdate,
)

# ==================== JournalEntryLineCreate Tests ====================


def test_journal_entry_line_create_valid():
    """Test vytvorenia validného JournalEntryLine."""
    line = JournalEntryLineCreate(
        line_number=1,
        account_id=1,
        partner_id=10,
        tax_rate_id=2,
        debit_amount=Decimal("1000.50"),
        credit_amount=Decimal("0.00"),
        description="Test line",
        currency_code="EUR",
    )
    assert line.line_number == 1
    assert line.account_id == 1
    assert line.debit_amount == Decimal("1000.50")
    assert line.credit_amount == Decimal("0.00")
    assert line.currency_code == "EUR"


def test_journal_entry_line_create_optional_fields():
    """Test že partner_id, tax_rate_id, description sú optional."""
    line = JournalEntryLineCreate(
        line_number=1,
        account_id=1,
        debit_amount=Decimal("500.00"),
        credit_amount=Decimal("0.00"),
        currency_code="USD",
    )
    assert line.partner_id is None
    assert line.tax_rate_id is None
    assert line.description is None


def test_journal_entry_line_create_negative_amount():
    """Test že záporné amounts sú rejected."""
    with pytest.raises(ValidationError) as exc:
        JournalEntryLineCreate(
            line_number=1,
            account_id=1,
            debit_amount=Decimal("-100.00"),
            credit_amount=Decimal("0.00"),
            currency_code="EUR",
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("debit_amount",) for e in errors)


def test_journal_entry_line_create_invalid_currency():
    """Test že currency_code musí mať 3 znaky."""
    with pytest.raises(ValidationError) as exc:
        JournalEntryLineCreate(
            line_number=1,
            account_id=1,
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("0.00"),
            currency_code="EU",  # Len 2 znaky
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("currency_code",) for e in errors)


# ==================== JournalEntryLineRead Tests ====================


def test_journal_entry_line_read_orm_mode():
    """Test ORM mode pre JournalEntryLineRead."""

    class MockLine:
        line_id = 1
        entry_id = 100
        line_number = 1
        account_id = 5
        partner_id = None
        tax_rate_id = None
        debit_amount = Decimal("1000.00")
        credit_amount = Decimal("0.00")
        description = "Mock line"
        currency_code = "EUR"

    line = JournalEntryLineRead.model_validate(MockLine())
    assert line.line_id == 1
    assert line.entry_id == 100
    assert line.debit_amount == Decimal("1000.00")


# ==================== JournalEntryLineUpdate Tests ====================


def test_journal_entry_line_update_partial():
    """Test že všetky fieldy v Update sú optional."""
    update = JournalEntryLineUpdate(debit_amount=Decimal("200.00"))
    assert update.debit_amount == Decimal("200.00")
    assert update.account_id is None
    assert update.description is None


# ==================== JournalEntryCreate Tests ====================


def test_journal_entry_create_valid():
    """Test vytvorenia validného JournalEntry s lines."""
    entry = JournalEntryCreate(
        batch_id=None,
        entry_number="DOC-001",
        entry_date=date(2024, 3, 30),
        description="Test document",
        created_by="admin",
        lines=[
            JournalEntryLineCreate(
                line_number=1,
                account_id=1,
                debit_amount=Decimal("1000.00"),
                credit_amount=Decimal("0.00"),
                currency_code="EUR",
            ),
            JournalEntryLineCreate(
                line_number=2,
                account_id=2,
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("1000.00"),
                currency_code="EUR",
            ),
        ],
    )
    assert entry.entry_number == "DOC-001"
    assert len(entry.lines) == 2
    assert entry.lines[0].debit_amount == Decimal("1000.00")
    assert entry.lines[1].credit_amount == Decimal("1000.00")


def test_journal_entry_create_no_lines():
    """Test že JournalEntry musí mať min. 2 lines (double-entry)."""
    with pytest.raises(ValidationError) as exc:
        JournalEntryCreate(
            entry_number="DOC-002",
            entry_date=date(2024, 3, 30),
            lines=[],  # Prázdny zoznam
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("lines",) for e in errors)


def test_journal_entry_create_single_line_rejected():
    """Test že JournalEntry s 1 line je rejected (min 2 pre double-entry)."""
    with pytest.raises(ValidationError) as exc:
        JournalEntryCreate(
            entry_number="DOC-002b",
            entry_date=date(2024, 3, 30),
            lines=[
                JournalEntryLineCreate(
                    line_number=1,
                    account_id=1,
                    debit_amount=Decimal("100.00"),
                    credit_amount=Decimal("0.00"),
                    currency_code="EUR",
                ),
            ],
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("lines",) for e in errors)


def test_journal_entry_create_optional_fields():
    """Test že batch_id, description, created_by sú optional."""
    entry = JournalEntryCreate(
        entry_number="DOC-003",
        entry_date=date(2024, 3, 30),
        lines=[
            JournalEntryLineCreate(
                line_number=1,
                account_id=1,
                debit_amount=Decimal("100.00"),
                credit_amount=Decimal("0.00"),
                currency_code="EUR",
            ),
            JournalEntryLineCreate(
                line_number=2,
                account_id=2,
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("100.00"),
                currency_code="EUR",
            ),
        ],
    )
    assert entry.batch_id is None
    assert entry.description is None
    assert entry.created_by is None


# ==================== JournalEntryRead Tests ====================


def test_journal_entry_read_orm_mode():
    """Test ORM mode pre JournalEntryRead."""

    class MockEntry:
        entry_id = 1
        batch_id = None
        entry_number = "DOC-001"
        entry_date = date(2024, 3, 30)
        description = "Mock entry"
        created_by = "admin"
        created_at = datetime(2024, 3, 30, 10, 0, 0, tzinfo=UTC)
        lines = []

    entry = JournalEntryRead.model_validate(MockEntry())
    assert entry.entry_id == 1
    assert entry.entry_number == "DOC-001"
    assert entry.lines == []


# ==================== JournalEntryUpdate Tests ====================


def test_journal_entry_update_partial():
    """Test že JournalEntryUpdate má všetky fieldy optional."""
    update = JournalEntryUpdate(description="Updated description")
    assert update.description == "Updated description"
    assert update.entry_date is None
