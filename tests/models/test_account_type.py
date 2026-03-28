"""Tests for AccountType model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.account_type import AccountType


def test_create_account_types(db_session):
    """Test creating standard account types."""
    asset = AccountType(
        code="ASSET",
        name="Assets",
        description="Economic resources controlled by the entity",
    )
    db_session.add(asset)

    liability = AccountType(
        code="LIABILITY",
        name="Liabilities",
        description="Present obligations of the entity",
    )
    db_session.add(liability)

    db_session.commit()

    # Verify retrieval
    fetched_asset = db_session.query(AccountType).filter_by(code="ASSET").first()
    assert fetched_asset is not None
    assert fetched_asset.name == "Assets"
    assert fetched_asset.description is not None

    fetched_liability = db_session.query(AccountType).filter_by(code="LIABILITY").first()
    assert fetched_liability is not None
    assert fetched_liability.name == "Liabilities"


def test_unique_code_constraint(db_session):
    """Test UNIQUE constraint on code column."""
    asset1 = AccountType(code="ASSET", name="Assets")
    db_session.add(asset1)
    db_session.commit()

    # Attempt to create duplicate code
    asset2 = AccountType(code="ASSET", name="Assets Duplicate")
    db_session.add(asset2)

    with pytest.raises((IntegrityError, Exception)):
        db_session.commit()

    db_session.rollback()


def test_nullable_description(db_session):
    """Test description column is nullable."""
    account_type = AccountType(code="EQUITY", name="Equity")  # No description
    db_session.add(account_type)
    db_session.commit()

    fetched = db_session.query(AccountType).filter_by(code="EQUITY").first()
    assert fetched is not None
    assert fetched.description is None


def test_account_type_repr(db_session):
    """Test __repr__ method."""
    account_type = AccountType(code="REVENUE", name="Revenue")
    db_session.add(account_type)
    db_session.commit()

    repr_str = repr(account_type)
    assert "REVENUE" in repr_str
    assert "Revenue" in repr_str
