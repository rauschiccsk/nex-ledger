"""
Tests for JournalEntryService.

Tests require the full FK chain:
ChartOfAccounts → AccountType + Currency + Account → JournalEntry → JournalEntryLine
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
    """Create prerequisite chart, account type, currency, and accounts."""
    chart = ChartOfAccounts(code="TEST-SVC", name="Test Chart for Service")
    db_session.add(chart)
    db_session.flush()

    acc_type = AccountType(code="ASSET-SVC", name="Asset (svc test)")
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
    account_extra = Account(
        chart_id=chart.chart_id,
        account_number="1020",
        name="Bank",
        account_type_id=acc_type.account_type_id,
        currency_code="EUR",
        level=1,
    )
    db_session.add_all([account_debit, account_credit, account_extra])
    db_session.flush()

    return {
        "chart": chart,
        "acc_type": acc_type,
        "currency": currency,
        "account_debit": account_debit,
        "account_credit": account_credit,
        "account_extra": account_extra,
    }


def test_validate_balanced_entry(db_session, setup_accounts):
    """Test validation of balanced journal entry."""
    accs = setup_accounts

    entry = JournalEntry(
        entry_number="SVC-BAL-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Test balanced entry",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.flush()

    debit_line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=accs["account_debit"].account_id,
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("0.00"),
        currency_code="EUR",
        description="Debit line",
    )
    credit_line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=2,
        account_id=accs["account_credit"].account_id,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("100.00"),
        currency_code="EUR",
        description="Credit line",
    )
    db_session.add_all([debit_line, credit_line])
    db_session.commit()

    # Should not raise
    result = JournalEntryService.validate_double_entry(db_session, entry.entry_id)
    assert result is True


def test_validate_unbalanced_entry(db_session, setup_accounts):
    """Test validation rejects unbalanced entry."""
    accs = setup_accounts

    entry = JournalEntry(
        entry_number="SVC-UNBAL-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Test unbalanced entry",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.flush()

    debit_line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=accs["account_debit"].account_id,
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("0.00"),
        currency_code="EUR",
        description="Debit line",
    )
    credit_line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=2,
        account_id=accs["account_credit"].account_id,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("50.00"),
        currency_code="EUR",
        description="Credit line",
    )
    db_session.add_all([debit_line, credit_line])
    db_session.commit()

    with pytest.raises(ValueError, match="unbalanced"):
        JournalEntryService.validate_double_entry(db_session, entry.entry_id)


def test_validate_no_lines_raises(db_session, setup_accounts):
    """Test validation raises when entry has no lines."""
    entry = JournalEntry(
        entry_number="SVC-EMPTY-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Entry with no lines",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.commit()

    with pytest.raises(ValueError, match="No lines found"):
        JournalEntryService.validate_double_entry(db_session, entry.entry_id)


def test_get_entry_balance(db_session, setup_accounts):
    """Test balance calculation returns correct totals."""
    accs = setup_accounts

    entry = JournalEntry(
        entry_number="SVC-BALANCE-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Test balance calculation",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.flush()

    lines = [
        JournalEntryLine(
            entry_id=entry.entry_id,
            line_number=1,
            account_id=accs["account_debit"].account_id,
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("0.00"),
            currency_code="EUR",
            description="Debit 1",
        ),
        JournalEntryLine(
            entry_id=entry.entry_id,
            line_number=2,
            account_id=accs["account_extra"].account_id,
            debit_amount=Decimal("50.00"),
            credit_amount=Decimal("0.00"),
            currency_code="EUR",
            description="Debit 2",
        ),
        JournalEntryLine(
            entry_id=entry.entry_id,
            line_number=3,
            account_id=accs["account_credit"].account_id,
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("150.00"),
            currency_code="EUR",
            description="Credit",
        ),
    ]
    db_session.add_all(lines)
    db_session.commit()

    total_debit, total_credit = JournalEntryService.get_entry_balance(
        db_session, entry.entry_id
    )

    assert total_debit == Decimal("150.00")
    assert total_credit == Decimal("150.00")


def test_get_entry_balance_empty(db_session, setup_accounts):
    """Test balance calculation returns zeros for entry with no lines."""
    entry = JournalEntry(
        entry_number="SVC-EMPTY-BAL-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Entry with no lines for balance",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.commit()

    total_debit, total_credit = JournalEntryService.get_entry_balance(
        db_session, entry.entry_id
    )

    assert total_debit == Decimal("0.00")
    assert total_credit == Decimal("0.00")
    assert isinstance(total_debit, Decimal)
    assert isinstance(total_credit, Decimal)
