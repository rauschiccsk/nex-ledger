"""Tests for OpeningBalance model.

Covers: CRUD, unique constraint, CASCADE delete (period + account),
server defaults, and __repr__.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.accounting_period import AccountingPeriod
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.opening_balance import OpeningBalance


def _create_dependencies(db_session):
    """Create FK dependencies needed for OpeningBalance tests.

    Returns:
        tuple: (period, account)
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

    # AccountingPeriod
    period = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2025,
        period_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
    db_session.add(period)
    db_session.flush()

    # Account
    account = Account(
        chart_id=chart.chart_id,
        account_number="211000",
        name="Pokladnica",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.flush()

    return period, account


def test_create_opening_balance(db_session) -> None:
    """Test creating an OpeningBalance with debit_amount=1000.00, credit_amount=0."""
    period, account = _create_dependencies(db_session)

    ob = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
        debit_amount=Decimal("1000.00"),
        credit_amount=Decimal("0.00"),
    )
    db_session.add(ob)
    db_session.commit()

    # Verify persisted
    assert ob.balance_id is not None
    assert ob.period_id == period.period_id
    assert ob.account_id == account.account_id
    assert ob.debit_amount == Decimal("1000.00")
    assert ob.credit_amount == Decimal("0.00")
    assert isinstance(ob.created_at, datetime)


def test_unique_constraint(db_session) -> None:
    """Test that duplicate (period_id, account_id) raises IntegrityError."""
    period, account = _create_dependencies(db_session)

    ob1 = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
        debit_amount=Decimal("500.00"),
    )
    db_session.add(ob1)
    db_session.commit()

    # Attempt duplicate — same period + account
    ob2 = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
        debit_amount=Decimal("200.00"),
    )
    db_session.add(ob2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_cascade_delete_period(db_session) -> None:
    """Test CASCADE: deleting period also deletes its opening balances."""
    period, account = _create_dependencies(db_session)

    ob = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
        debit_amount=Decimal("750.00"),
    )
    db_session.add(ob)
    db_session.commit()

    balance_id = ob.balance_id

    # Delete period via raw SQL (CASCADE should remove opening_balance)
    db_session.execute(
        text("DELETE FROM accounting_period WHERE period_id = :id"),
        {"id": period.period_id},
    )
    db_session.commit()

    # Verify opening balance was cascaded
    result = db_session.execute(
        text("SELECT COUNT(*) FROM opening_balance WHERE balance_id = :id"),
        {"id": balance_id},
    )
    assert result.scalar() == 0


def test_cascade_delete_account(db_session) -> None:
    """Test CASCADE: deleting account also deletes its opening balances."""
    period, account = _create_dependencies(db_session)

    ob = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
        credit_amount=Decimal("3000.00"),
    )
    db_session.add(ob)
    db_session.commit()

    balance_id = ob.balance_id

    # Delete account via raw SQL (CASCADE should remove opening_balance)
    db_session.execute(
        text("DELETE FROM account WHERE account_id = :id"),
        {"id": account.account_id},
    )
    db_session.commit()

    # Verify opening balance was cascaded
    result = db_session.execute(
        text("SELECT COUNT(*) FROM opening_balance WHERE balance_id = :id"),
        {"id": balance_id},
    )
    assert result.scalar() == 0


def test_server_defaults(db_session) -> None:
    """Test that debit_amount and credit_amount default to 0 when not specified."""
    period, account = _create_dependencies(db_session)

    ob = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
    )
    db_session.add(ob)
    db_session.commit()

    # Refresh to get server defaults
    db_session.refresh(ob)

    assert ob.debit_amount == Decimal("0.00")
    assert ob.credit_amount == Decimal("0.00")
    assert ob.created_at is not None


def test_repr(db_session) -> None:
    """Test __repr__ output format."""
    period, account = _create_dependencies(db_session)

    ob = OpeningBalance(
        period_id=period.period_id,
        account_id=account.account_id,
        debit_amount=Decimal("1234.56"),
        credit_amount=Decimal("0.00"),
    )
    db_session.add(ob)
    db_session.commit()

    result = repr(ob)
    assert "OpeningBalance" in result
    assert f"balance_id={ob.balance_id}" in result
    assert f"period_id={period.period_id}" in result
    assert f"account_id={account.account_id}" in result
    assert "debit=" in result
    assert "credit=" in result
