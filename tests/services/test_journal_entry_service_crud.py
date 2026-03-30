"""
Tests for JournalEntryService CRUD operations.

Tests require the full FK chain:
ChartOfAccounts -> AccountType + Currency + Account -> JournalEntry -> JournalEntryLine
"""
import datetime
from decimal import Decimal

import pytest

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.services.journal_entry_service import JournalEntryService


@pytest.fixture()
def setup_accounts(db_session):
    """Create prerequisite chart, account type, currency, and two accounts."""
    chart = ChartOfAccounts(code="CRUD-TEST", name="Chart for CRUD tests")
    db_session.add(chart)
    db_session.flush()

    acc_type = AccountType(code="ASSET-CRUD", name="Asset (crud)")
    db_session.add(acc_type)
    db_session.flush()

    currency = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(currency)
    db_session.flush()

    account_debit = Account(
        chart_id=chart.chart_id,
        account_number="1010",
        name="Cash",
        account_type_id=acc_type.account_type_id,
        currency_code="EUR",
        level=1,
    )
    account_credit = Account(
        chart_id=chart.chart_id,
        account_number="2010",
        name="Revenue",
        account_type_id=acc_type.account_type_id,
        currency_code="EUR",
        level=1,
    )
    db_session.add_all([account_debit, account_credit])
    db_session.flush()

    return {
        "chart": chart,
        "acc_type": acc_type,
        "currency": currency,
        "account_debit": account_debit,
        "account_credit": account_credit,
    }


# ──────────────────────────────────────────────
# list_entries
# ──────────────────────────────────────────────


def test_list_entries_empty(db_session):
    """list_entries returns empty list and zero count on empty DB."""
    entries, total = JournalEntryService.list_entries(db_session)
    assert entries == []
    assert total == 0


def test_list_entries_with_data(db_session, setup_accounts):
    """list_entries returns entries ordered by date DESC, id DESC."""
    e1 = JournalEntry(
        entry_number="CRUD-LIST-001",
        entry_date=datetime.date(2026, 1, 1),
        description="First",
    )
    e2 = JournalEntry(
        entry_number="CRUD-LIST-002",
        entry_date=datetime.date(2026, 6, 15),
        description="Second",
    )
    db_session.add_all([e1, e2])
    db_session.flush()

    entries, total = JournalEntryService.list_entries(db_session)
    assert total == 2
    assert len(entries) == 2
    # Most recent date first
    assert entries[0].entry_number == "CRUD-LIST-002"
    assert entries[1].entry_number == "CRUD-LIST-001"


def test_list_entries_pagination(db_session, setup_accounts):
    """list_entries respects skip and limit parameters."""
    for i in range(5):
        db_session.add(
            JournalEntry(
                entry_number=f"CRUD-PAGE-{i:03d}",
                entry_date=datetime.date(2026, 1, 1 + i),
            )
        )
    db_session.flush()

    entries, total = JournalEntryService.list_entries(db_session, skip=1, limit=2)
    assert total == 5
    assert len(entries) == 2


# ──────────────────────────────────────────────
# get_entry
# ──────────────────────────────────────────────


def test_get_entry_success(db_session, setup_accounts):
    """get_entry returns entry by ID."""
    entry = JournalEntry(
        entry_number="CRUD-GET-001",
        entry_date=datetime.date(2026, 3, 1),
        description="Test get",
    )
    db_session.add(entry)
    db_session.flush()

    result = JournalEntryService.get_entry(db_session, entry.entry_id)
    assert result.entry_id == entry.entry_id
    assert result.entry_number == "CRUD-GET-001"


def test_get_entry_not_found(db_session):
    """get_entry raises ValueError for nonexistent entry."""
    with pytest.raises(ValueError, match="Journal entry 99999 not found"):
        JournalEntryService.get_entry(db_session, 99999)


# ──────────────────────────────────────────────
# create_entry
# ──────────────────────────────────────────────


def test_create_entry_without_lines(db_session, setup_accounts):
    """create_entry creates an entry without lines."""
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-CREATE-001",
            "entry_date": datetime.date(2026, 3, 1),
            "description": "No lines",
        },
    )
    assert entry.entry_id is not None
    assert entry.entry_number == "CRUD-CREATE-001"


def test_create_entry_with_lines(db_session, setup_accounts):
    """create_entry creates entry + balanced lines in one call."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-CREATE-002",
            "entry_date": datetime.date(2026, 3, 2),
            "description": "With lines",
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("200.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("200.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    assert entry.entry_id is not None
    lines = JournalEntryService.list_lines(db_session, entry.entry_id)
    assert len(lines) == 2


def test_create_entry_unbalanced_lines_raises(db_session, setup_accounts):
    """create_entry raises ValueError when lines don't balance."""
    accs = setup_accounts
    with pytest.raises(ValueError, match="unbalanced"):
        JournalEntryService.create_entry(
            db_session,
            {
                "entry_number": "CRUD-CREATE-FAIL",
                "entry_date": datetime.date(2026, 3, 3),
                "lines": [
                    {
                        "line_number": 1,
                        "account_id": accs["account_debit"].account_id,
                        "debit_amount": Decimal("100.00"),
                        "credit_amount": Decimal("0.00"),
                        "currency_code": "EUR",
                    },
                    {
                        "line_number": 2,
                        "account_id": accs["account_credit"].account_id,
                        "debit_amount": Decimal("0.00"),
                        "credit_amount": Decimal("50.00"),
                        "currency_code": "EUR",
                    },
                ],
            },
        )


# ──────────────────────────────────────────────
# update_entry
# ──────────────────────────────────────────────


def test_update_entry_success(db_session, setup_accounts):
    """update_entry modifies entry attributes."""
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-UPD-001",
            "entry_date": datetime.date(2026, 3, 1),
            "description": "Original",
        },
    )
    updated = JournalEntryService.update_entry(
        db_session,
        entry.entry_id,
        {"description": "Updated", "entry_date": datetime.date(2026, 4, 1)},
    )
    assert updated.description == "Updated"
    assert updated.entry_date == datetime.date(2026, 4, 1)


# ──────────────────────────────────────────────
# delete_entry
# ──────────────────────────────────────────────


def test_delete_entry_success(db_session, setup_accounts):
    """delete_entry removes entry and its lines."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-DEL-001",
            "entry_date": datetime.date(2026, 3, 1),
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("50.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("50.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    eid = entry.entry_id
    JournalEntryService.delete_entry(db_session, eid)

    with pytest.raises(ValueError, match="not found"):
        JournalEntryService.get_entry(db_session, eid)

    lines = (
        db_session.query(JournalEntryLine)
        .filter(JournalEntryLine.entry_id == eid)
        .all()
    )
    assert lines == []


# ──────────────────────────────────────────────
# list_lines
# ──────────────────────────────────────────────


def test_list_lines_success(db_session, setup_accounts):
    """list_lines returns all lines for a given entry."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-LL-001",
            "entry_date": datetime.date(2026, 3, 1),
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("300.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("300.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    lines = JournalEntryService.list_lines(db_session, entry.entry_id)
    assert len(lines) == 2


# ──────────────────────────────────────────────
# get_line
# ──────────────────────────────────────────────


def test_get_line_success(db_session, setup_accounts):
    """get_line returns the correct line."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-GL-001",
            "entry_date": datetime.date(2026, 3, 1),
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("100.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("100.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    lines = JournalEntryService.list_lines(db_session, entry.entry_id)
    line = JournalEntryService.get_line(db_session, entry.entry_id, lines[0].line_id)
    assert line.line_id == lines[0].line_id


def test_get_line_not_found(db_session, setup_accounts):
    """get_line raises ValueError when line does not exist."""
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-GL-NF",
            "entry_date": datetime.date(2026, 3, 1),
        },
    )
    with pytest.raises(ValueError, match="not found or does not belong"):
        JournalEntryService.get_line(db_session, entry.entry_id, 99999)


def test_get_line_wrong_entry(db_session, setup_accounts):
    """get_line raises ValueError when line belongs to different entry."""
    accs = setup_accounts
    entry1 = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-GL-WE1",
            "entry_date": datetime.date(2026, 3, 1),
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("100.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("100.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    entry2 = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-GL-WE2",
            "entry_date": datetime.date(2026, 3, 1),
        },
    )
    lines = JournalEntryService.list_lines(db_session, entry1.entry_id)
    # Line from entry1, but querying with entry2 ID
    with pytest.raises(ValueError, match="does not belong"):
        JournalEntryService.get_line(db_session, entry2.entry_id, lines[0].line_id)


# ──────────────────────────────────────────────
# create_line + revalidation
# ──────────────────────────────────────────────


def test_create_line_revalidation(db_session, setup_accounts):
    """create_line validates double-entry after adding a balanced pair."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-CL-001",
            "entry_date": datetime.date(2026, 3, 1),
        },
    )

    # First line alone is unbalanced — but create_line validates, so add a pair
    # We add debit first; validate_double_entry will fail
    with pytest.raises(ValueError, match="unbalanced"):
        JournalEntryService.create_line(
            db_session,
            entry.entry_id,
            {
                "line_number": 1,
                "account_id": accs["account_debit"].account_id,
                "debit_amount": Decimal("100.00"),
                "credit_amount": Decimal("0.00"),
                "currency_code": "EUR",
            },
        )


# ──────────────────────────────────────────────
# update_line + revalidation
# ──────────────────────────────────────────────


def test_update_line_revalidation(db_session, setup_accounts):
    """update_line revalidates balance after modification."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-UL-001",
            "entry_date": datetime.date(2026, 3, 1),
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("100.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("100.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    lines = JournalEntryService.list_lines(db_session, entry.entry_id)

    # Unbalance by changing debit amount
    with pytest.raises(ValueError, match="unbalanced"):
        JournalEntryService.update_line(
            db_session,
            entry.entry_id,
            lines[0].line_id,
            {"debit_amount": Decimal("999.00")},
        )


# ──────────────────────────────────────────────
# delete_line + revalidation
# ──────────────────────────────────────────────


def test_delete_line_revalidation(db_session, setup_accounts):
    """delete_line revalidates balance if remaining lines exist."""
    accs = setup_accounts
    entry = JournalEntryService.create_entry(
        db_session,
        {
            "entry_number": "CRUD-DL-001",
            "entry_date": datetime.date(2026, 3, 1),
            "lines": [
                {
                    "line_number": 1,
                    "account_id": accs["account_debit"].account_id,
                    "debit_amount": Decimal("100.00"),
                    "credit_amount": Decimal("0.00"),
                    "currency_code": "EUR",
                },
                {
                    "line_number": 2,
                    "account_id": accs["account_credit"].account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": Decimal("100.00"),
                    "currency_code": "EUR",
                },
            ],
        },
    )
    lines = JournalEntryService.list_lines(db_session, entry.entry_id)

    # Deleting one line leaves the entry unbalanced
    with pytest.raises(ValueError, match="unbalanced"):
        JournalEntryService.delete_line(
            db_session, entry.entry_id, lines[0].line_id
        )
