"""
Tests for AccountService.

Tests account balance reconciliation and statement generation.
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
from app.services.account_service import AccountService


@pytest.fixture()
def setup_account(db_session):
    """Create test account with full FK chain."""
    chart = ChartOfAccounts(code="TEST-ACCSVC", name="Test Chart for AccSvc")
    db_session.add(chart)
    db_session.flush()

    acc_type = AccountType(code="ASSET-ACCSVC", name="Asset (accsvc test)")
    db_session.add(acc_type)
    db_session.flush()

    currency = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(currency)
    db_session.flush()

    account = Account(
        chart_id=chart.chart_id,
        account_number="1000",
        name="Test Account",
        account_type_id=acc_type.account_type_id,
        currency_code="EUR",
        level=1,
        opening_balance=Decimal("1000.00"),
        current_balance=Decimal("1000.00"),
    )
    db_session.add(account)
    db_session.flush()

    return account


def test_recalculate_balance(db_session, setup_account):
    """Test balance recalculation with debit and credit lines."""
    account = setup_account

    entry = JournalEntry(
        entry_number="ACCSVC-BAL-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Test entry",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.flush()

    # Add debit line (+500)
    line1 = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account.account_id,
        debit_amount=Decimal("500.00"),
        credit_amount=Decimal("0.00"),
        currency_code="EUR",
    )
    db_session.add(line1)

    # Add credit line (-200)
    line2 = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=2,
        account_id=account.account_id,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("200.00"),
        currency_code="EUR",
    )
    db_session.add(line2)
    db_session.commit()

    # Recalculate balance
    result = AccountService.recalculate_balance(db_session, account_id=account.account_id)

    # Verify: 1000 (opening) + 500 (debit) - 200 (credit) = 1300
    assert result.current_balance == Decimal("1300.00")


def test_get_account_statement(db_session, setup_account):
    """Test account statement generation with date filtering."""
    account = setup_account

    # Create 3 journal entries on different dates
    for i in range(3):
        entry = JournalEntry(
            entry_number=f"ACCSVC-STMT-{i+1:03d}",
            entry_date=datetime.date(2026, 3, 26 + i),
            description=f"Entry {i+1}",
            created_by="test_user",
        )
        db_session.add(entry)
        db_session.flush()

        line = JournalEntryLine(
            entry_id=entry.entry_id,
            line_number=1,
            account_id=account.account_id,
            debit_amount=Decimal("100.00") if i % 2 == 0 else Decimal("0.00"),
            credit_amount=Decimal("0.00") if i % 2 == 0 else Decimal("50.00"),
            currency_code="EUR",
        )
        db_session.add(line)
    db_session.commit()

    # Get statement for middle date only (2026-03-27)
    statement = AccountService.get_account_statement(
        db_session,
        account_id=account.account_id,
        from_date=datetime.date(2026, 3, 27),
        to_date=datetime.date(2026, 3, 27),
    )

    # Should return only 1 transaction
    assert len(statement) == 1
    assert statement[0]["date"] == datetime.date(2026, 3, 27)
    assert statement[0]["credit"] == Decimal("50.00")
    # Running balance: 1000 (opening) - 50 = 950
    assert statement[0]["balance"] == Decimal("950.00")


def test_numeric_precision(db_session, setup_account):
    """Test Decimal precision (no floating point errors)."""
    account = setup_account

    entry = JournalEntry(
        entry_number="ACCSVC-PREC-001",
        entry_date=datetime.date(2026, 3, 28),
        description="Precision test",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.flush()

    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account.account_id,
        debit_amount=Decimal("0.10"),
        credit_amount=Decimal("0.00"),
        currency_code="EUR",
    )
    db_session.add(line)
    db_session.commit()

    result = AccountService.recalculate_balance(db_session, account_id=account.account_id)

    # Verify: 1000.00 + 0.10 = 1000.10 (exact, no 1000.10000000001)
    assert result.current_balance == Decimal("1000.10")
    assert str(result.current_balance) == "1000.10"


def test_recalculate_balance_not_found(db_session):
    """Test error handling for non-existent account."""
    with pytest.raises(ValueError, match="Account 999 not found"):
        AccountService.recalculate_balance(db_session, account_id=999)


def test_get_statement_not_found(db_session):
    """Test error handling for non-existent account in statement."""
    with pytest.raises(ValueError, match="Account 999 not found"):
        AccountService.get_account_statement(
            db_session,
            account_id=999,
            from_date=datetime.date(2026, 1, 1),
            to_date=datetime.date(2026, 12, 31),
        )
