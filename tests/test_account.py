"""Tests for Account model."""

from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.account import Account
from app.models.account_type import AccountCategory, AccountType, NormalBalance
from app.models.currency import Currency


def _make_currency(db_session, code="EUR", name="Euro", symbol="\u20ac", decimal_places=2):
    """Helper to create a currency."""
    currency = Currency(code=code, name=name, symbol=symbol, decimal_places=decimal_places)
    db_session.add(currency)
    db_session.flush()
    return currency


def _make_account_type(
    db_session,
    code="ASSET",
    name="Asset Account",
    category=AccountCategory.ASSET,
    normal_balance=NormalBalance.DEBIT,
):
    """Helper to create an account type."""
    account_type = AccountType(
        code=code, name=name, category=category, normal_balance=normal_balance
    )
    db_session.add(account_type)
    db_session.flush()
    return account_type


def test_create_account(db_session):
    """Test creating account with FK relationships."""
    currency = _make_currency(db_session)
    account_type = _make_account_type(db_session)

    account = Account(
        code="1000",
        name="Cash",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(account)
    db_session.commit()

    assert isinstance(account.id, UUID)
    assert account.code == "1000"
    assert account.name == "Cash"
    assert account.account_type.code == "ASSET"
    assert account.currency.code == "EUR"

    # Verify is_active defaults to True
    db_session.expire(account)
    assert account.is_active is True


def test_account_code_unique(db_session):
    """Test UNIQUE constraint on code."""
    currency = _make_currency(db_session, code="USD", name="US Dollar", symbol="$")
    account_type = _make_account_type(
        db_session,
        code="EXPENSE",
        name="Expense",
        category=AccountCategory.EXPENSE,
        normal_balance=NormalBalance.DEBIT,
    )

    account1 = Account(
        code="5000",
        name="Travel Expense",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(account1)
    db_session.commit()

    account2 = Account(
        code="5000",
        name="Duplicate",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(account2)
    with pytest.raises(IntegrityError, match="uq_account_code"):
        db_session.commit()


def test_fk_account_type_restrict(db_session):
    """Test FK RESTRICT on account_type_id — cannot delete type if accounts exist."""
    currency = _make_currency(db_session, code="CZK", name="Czech Koruna", symbol="K\u010d")
    account_type = _make_account_type(
        db_session,
        code="LIABILITY",
        name="Liability",
        category=AccountCategory.LIABILITY,
        normal_balance=NormalBalance.CREDIT,
    )

    account = Account(
        code="2000",
        name="Accounts Payable",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(account)
    db_session.commit()

    # Use raw SQL to bypass ORM cascade (which tries to NULL the FK first).
    # pg8000 maps FK violation (23503) to ProgrammingError, not IntegrityError.
    with pytest.raises((IntegrityError, ProgrammingError), match="account_account_type_id_fkey"):
        db_session.execute(
            text("DELETE FROM account_type WHERE id = :id"),
            {"id": str(account_type.id)},
        )


def test_fk_currency_restrict(db_session):
    """Test FK RESTRICT on currency_id — cannot delete currency if accounts exist."""
    currency = _make_currency(db_session, code="GBP", name="British Pound", symbol="\u00a3")
    account_type = _make_account_type(
        db_session,
        code="REVENUE",
        name="Revenue",
        category=AccountCategory.REVENUE,
        normal_balance=NormalBalance.CREDIT,
    )

    account = Account(
        code="4000",
        name="Sales Revenue",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(account)
    db_session.commit()

    # Use raw SQL to bypass ORM cascade (which tries to NULL the FK first).
    # pg8000 maps FK violation (23503) to ProgrammingError, not IntegrityError.
    with pytest.raises((IntegrityError, ProgrammingError), match="account_currency_id_fkey"):
        db_session.execute(
            text("DELETE FROM currency WHERE id = :id"),
            {"id": str(currency.id)},
        )


def test_sub_account_hierarchy(db_session):
    """Test parent-child account hierarchy."""
    currency = _make_currency(db_session)
    account_type = _make_account_type(db_session)

    parent = Account(
        code="1000",
        name="Cash",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(parent)
    db_session.flush()

    sub_account = Account(
        code="1010",
        name="Petty Cash",
        account_type_id=account_type.id,
        currency_id=currency.id,
        parent_account_id=parent.id,
    )
    db_session.add(sub_account)
    db_session.commit()

    assert sub_account.parent_account.code == "1000"
    assert len(parent.sub_accounts) == 1
    assert parent.sub_accounts[0].code == "1010"


def test_parent_delete_cascade(db_session):
    """Test CASCADE delete — deleting parent account deletes sub-accounts."""
    currency = _make_currency(db_session, code="USD", name="US Dollar", symbol="$")
    account_type = _make_account_type(
        db_session,
        code="EQUITY",
        name="Equity",
        category=AccountCategory.EQUITY,
        normal_balance=NormalBalance.CREDIT,
    )

    parent = Account(
        code="3000",
        name="Retained Earnings",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    db_session.add(parent)
    db_session.flush()

    sub1 = Account(
        code="3010",
        name="Current Year",
        account_type_id=account_type.id,
        currency_id=currency.id,
        parent_account_id=parent.id,
    )
    sub2 = Account(
        code="3020",
        name="Prior Years",
        account_type_id=account_type.id,
        currency_id=currency.id,
        parent_account_id=parent.id,
    )
    db_session.add_all([sub1, sub2])
    db_session.commit()

    parent_id = parent.id
    sub1_id = sub1.id
    sub2_id = sub2.id

    db_session.delete(parent)
    db_session.commit()

    # Verify CASCADE — sub-accounts deleted
    assert db_session.get(Account, parent_id) is None
    assert db_session.get(Account, sub1_id) is None
    assert db_session.get(Account, sub2_id) is None


def test_account_repr(db_session):
    """Test __repr__ method."""
    currency = _make_currency(db_session)
    account_type = _make_account_type(db_session)

    account = Account(
        code="1100",
        name="Bank Account",
        account_type_id=account_type.id,
        currency_id=currency.id,
    )
    assert "Account(code='1100'" in repr(account)
    assert "name='Bank Account'" in repr(account)
