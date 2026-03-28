"""Tests for AccountType model."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.account_type import AccountCategory, AccountType, NormalBalance


def test_create_account_type(db_session):
    """Test creating account type with all fields."""
    account_type = AccountType(
        code="ASSET-CASH",
        name="Cash",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
        is_system=True,
    )
    db_session.add(account_type)
    db_session.commit()

    assert account_type.id is not None
    assert account_type.code == "ASSET-CASH"
    assert account_type.category == AccountCategory.ASSET
    assert account_type.normal_balance == NormalBalance.DEBIT
    assert account_type.is_system is True


def test_unique_code_constraint(db_session):
    """Test UNIQUE constraint on code."""
    account_type1 = AccountType(
        code="ASSET-BANK",
        name="Bank Account",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(account_type1)
    db_session.commit()

    account_type2 = AccountType(
        code="ASSET-BANK",  # Duplicate code
        name="Another Bank",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(account_type2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_category_enum(db_session):
    """Test all valid category values."""
    categories = [
        ("ASSET-TEST", AccountCategory.ASSET, NormalBalance.DEBIT),
        ("LIAB-TEST", AccountCategory.LIABILITY, NormalBalance.CREDIT),
        ("EQUITY-TEST", AccountCategory.EQUITY, NormalBalance.CREDIT),
        ("REV-TEST", AccountCategory.REVENUE, NormalBalance.CREDIT),
        ("EXP-TEST", AccountCategory.EXPENSE, NormalBalance.DEBIT),
    ]

    for code, category, balance in categories:
        account_type = AccountType(
            code=code,
            name=f"Test {category.value}",
            category=category,
            normal_balance=balance,
        )
        db_session.add(account_type)

    db_session.commit()

    result = db_session.execute(select(AccountType)).scalars().all()
    assert len(result) == 5


def test_normal_balance_enum(db_session):
    """Test both valid normal_balance values."""
    debit_type = AccountType(
        code="DEBIT-TEST",
        name="Debit Test",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    credit_type = AccountType(
        code="CREDIT-TEST",
        name="Credit Test",
        category=AccountCategory.LIABILITY,
        normal_balance=NormalBalance.CREDIT,
    )
    db_session.add_all([debit_type, credit_type])
    db_session.commit()

    assert debit_type.normal_balance == NormalBalance.DEBIT
    assert credit_type.normal_balance == NormalBalance.CREDIT


def test_default_is_system_false(db_session):
    """Test is_system defaults to false."""
    account_type = AccountType(
        code="USER-TYPE",
        name="User Type",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(account_type)
    db_session.commit()

    # Re-fetch to get DB default
    db_session.expire(account_type)
    assert account_type.is_system is False


def test_repr(db_session):
    """Test __repr__ output."""
    account_type = AccountType(
        code="REPR-TEST",
        name="Repr Test",
        category=AccountCategory.EXPENSE,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(account_type)
    db_session.commit()

    assert repr(account_type) == "<AccountType REPR-TEST: Repr Test (expense)>"


def test_timestamps(db_session):
    """Test created_at and updated_at are populated."""
    account_type = AccountType(
        code="TIME-TEST",
        name="Timestamp Test",
        category=AccountCategory.REVENUE,
        normal_balance=NormalBalance.CREDIT,
    )
    db_session.add(account_type)
    db_session.commit()

    db_session.expire(account_type)
    assert account_type.created_at is not None
    assert account_type.updated_at is not None
