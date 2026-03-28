"""Tests for Account model."""

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency


def _create_dependencies(db_session):
    """Create common FK dependencies for Account tests."""
    chart = ChartOfAccounts(code="SK2025", name="Test Chart")
    db_session.add(chart)
    db_session.flush()

    account_type = AccountType(code="ASSET", name="Assets")
    db_session.add(account_type)
    db_session.flush()

    currency = Currency(currency_code="EUR", name="Euro")
    db_session.add(currency)
    db_session.flush()

    return chart, account_type, currency


def test_create_account(db_session):
    """Test creating an account with all required FK."""
    chart, account_type, currency = _create_dependencies(db_session)

    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.commit()

    assert account.account_id is not None
    assert account.chart_id == chart.chart_id
    assert account.account_number == "100"
    assert account.name == "Cash"
    assert account.is_active is True
    assert account.opening_balance == Decimal("0")
    assert account.current_balance == Decimal("0")
    assert account.updated_at is not None


def test_self_fk_parent_child(db_session):
    """Test hierarchical structure with parent-child accounts."""
    chart, account_type, currency = _create_dependencies(db_session)

    # Parent account (level 1, root)
    parent = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Current Assets",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        parent_account_id=None,
        level=1,
    )
    db_session.add(parent)
    db_session.flush()

    # Child account (level 2)
    child = Account(
        chart_id=chart.chart_id,
        account_number="101",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        parent_account_id=parent.account_id,
        level=2,
    )
    db_session.add(child)
    db_session.commit()

    assert parent.parent_account_id is None
    assert child.parent_account_id == parent.account_id
    assert parent.level == 1
    assert child.level == 2


def test_unique_constraint(db_session):
    """Test UNIQUE constraint on (chart_id, account_number)."""
    chart, account_type, currency = _create_dependencies(db_session)

    account1 = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account1)
    db_session.commit()

    # Duplicate account_number in same chart -> should fail
    account2 = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Another Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_fk_chart_id(db_session):
    """Test FK constraint — invalid chart_id should fail."""
    account = Account(
        chart_id=9999,
        account_number="100",
        name="Cash",
        account_type_id=1,
        currency_code="EUR",
        level=1,
    )
    db_session.add(account)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_fk_account_type_id(db_session):
    """Test FK constraint — invalid account_type_id should fail."""
    chart = ChartOfAccounts(code="FK-AT", name="FK Account Type Test")
    db_session.add(chart)
    db_session.flush()

    currency = Currency(currency_code="EUR", name="Euro")
    db_session.add(currency)
    db_session.flush()

    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=9999,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_fk_currency_code(db_session):
    """Test FK constraint — invalid currency_code should fail."""
    chart = ChartOfAccounts(code="FK-CUR", name="FK Currency Test")
    db_session.add(chart)
    db_session.flush()

    account_type = AccountType(code="ASSET", name="Assets")
    db_session.add(account_type)
    db_session.flush()

    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code="XXX",
        level=1,
    )
    db_session.add(account)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_cascade_delete(db_session):
    """Test CASCADE delete when chart is deleted."""
    chart, account_type, currency = _create_dependencies(db_session)

    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.commit()

    account_id = account.account_id

    # CASCADE delete via raw SQL (avoid ORM relationship issues)
    db_session.execute(
        text("DELETE FROM chart_of_accounts WHERE chart_id = :id"),
        {"id": chart.chart_id},
    )
    db_session.commit()

    deleted_account = db_session.get(Account, account_id)
    assert deleted_account is None


def test_set_null_on_parent_delete(db_session):
    """Test SET NULL when parent account is deleted."""
    chart, account_type, currency = _create_dependencies(db_session)

    # Parent account
    parent = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Current Assets",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(parent)
    db_session.flush()

    # Child account
    child = Account(
        chart_id=chart.chart_id,
        account_number="101",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        parent_account_id=parent.account_id,
        level=2,
    )
    db_session.add(child)
    db_session.commit()

    child_id = child.account_id
    parent_id = parent.account_id

    # Delete parent via raw SQL -> child.parent_account_id should become NULL
    db_session.execute(
        text("DELETE FROM account WHERE account_id = :id"),
        {"id": parent_id},
    )
    db_session.commit()

    # Expire child to force reload from DB
    db_session.expire(child)
    child_after = db_session.get(Account, child_id)
    assert child_after is not None
    assert child_after.parent_account_id is None


def test_default_values(db_session):
    """Test server_default values for boolean and numeric fields."""
    chart, account_type, currency = _create_dependencies(db_session)

    # Create account without specifying optional fields
    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.commit()

    # Refresh to get server defaults
    db_session.refresh(account)

    assert account.is_active is True
    assert account.opening_balance == Decimal("0")
    assert account.current_balance == Decimal("0")


def test_updated_at_auto_update(db_session):
    """Test updated_at is automatically updated on record change."""
    chart, account_type, currency = _create_dependencies(db_session)

    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.commit()

    original_updated_at = account.updated_at

    # Update account via raw SQL to trigger the DB trigger
    db_session.execute(
        text("UPDATE account SET name = 'Updated Cash' WHERE account_id = :id"),
        {"id": account.account_id},
    )
    db_session.commit()

    # Expire and reload to get fresh value from DB
    db_session.expire(account)
    db_session.refresh(account)

    assert account.updated_at >= original_updated_at
    assert account.name == "Updated Cash"


def test_repr(db_session):
    """Test __repr__ output."""
    chart, account_type, currency = _create_dependencies(db_session)

    account = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.commit()

    repr_str = repr(account)
    assert "Account" in repr_str
    assert f"account_id={account.account_id}" in repr_str
    assert f"chart_id={chart.chart_id}" in repr_str
    assert "account_number='100'" in repr_str
    assert "name='Cash'" in repr_str
