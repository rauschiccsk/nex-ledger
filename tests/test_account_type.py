"""Tests for AccountType model."""

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.account_type import AccountCategory, AccountType, NormalBalance


def test_insert_account_types(db_session):
    """Test vloženia základných typov účtov."""
    types = [
        AccountType(
            code="1XX",
            name="Aktíva",
            category=AccountCategory.ASSET,
            normal_balance=NormalBalance.DEBIT,
        ),
        AccountType(
            code="2XX",
            name="Pasíva",
            category=AccountCategory.LIABILITY,
            normal_balance=NormalBalance.CREDIT,
        ),
        AccountType(
            code="3XX",
            name="Vlastné imanie",
            category=AccountCategory.EQUITY,
            normal_balance=NormalBalance.CREDIT,
        ),
        AccountType(
            code="5XX",
            name="Náklady",
            category=AccountCategory.EXPENSE,
            normal_balance=NormalBalance.DEBIT,
        ),
        AccountType(
            code="6XX",
            name="Výnosy",
            category=AccountCategory.REVENUE,
            normal_balance=NormalBalance.CREDIT,
        ),
    ]

    for acc_type in types:
        db_session.add(acc_type)
    db_session.commit()

    assert db_session.query(AccountType).count() == 5
    asset_type = db_session.query(AccountType).filter_by(code="1XX").first()
    assert asset_type.name == "Aktíva"
    assert asset_type.category == AccountCategory.ASSET
    assert asset_type.normal_balance == NormalBalance.DEBIT
    assert asset_type.is_system is False


def test_unique_code_constraint(db_session):
    """Test UNIQUE constraint na code — duplikát musí zlyhať."""
    acc1 = AccountType(
        code="1XX",
        name="Aktíva",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(acc1)
    db_session.commit()

    acc2 = AccountType(
        code="1XX",
        name="Iné aktíva",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(acc2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_category_enum_constraint(db_session):
    """Test ENUM constraint na category — neplatná hodnota musí zlyhať."""
    # Python StrEnum odmietne neplatnú hodnotu
    with pytest.raises(ValueError):
        AccountCategory("invalid_category")


def test_normal_balance_enum_constraint(db_session):
    """Test ENUM constraint na normal_balance — neplatná hodnota musí zlyhať."""
    # Python StrEnum odmietne neplatnú hodnotu
    with pytest.raises(ValueError):
        NormalBalance("invalid_balance")


def test_is_system_default(db_session):
    """Test is_system DEFAULT false — nový typ nemá is_system flag."""
    acc = AccountType(
        code="TEST",
        name="Test",
        category=AccountCategory.ASSET,
        normal_balance=NormalBalance.DEBIT,
    )
    db_session.add(acc)
    db_session.commit()

    db_session.refresh(acc)
    assert acc.is_system is False
