"""Unit testy pre Account Pydantic schémy."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.schemas.account import AccountCreate, AccountRead, AccountUpdate


def test_account_create_valid():
    """Test vytvorenia AccountCreate s validnými dátami."""
    data = AccountCreate(
        chart_id=1,
        account_number="111",
        name="Hotovosť v pokladni",
        account_type_id=1,
        currency_code="EUR",
        parent_account_id=None,
        level=1,
        is_active=True,
        opening_balance=Decimal("1000.50"),
    )
    assert data.chart_id == 1
    assert data.account_number == "111"
    assert data.name == "Hotovosť v pokladni"
    assert data.account_type_id == 1
    assert data.currency_code == "EUR"
    assert data.parent_account_id is None
    assert data.level == 1
    assert data.is_active is True
    assert data.opening_balance == Decimal("1000.50")


def test_account_create_defaults():
    """Test default hodnôt v AccountCreate."""
    data = AccountCreate(
        chart_id=1,
        account_number="111",
        name="Test Account",
        account_type_id=1,
        currency_code="EUR",
        level=1,
    )
    assert data.is_active is True
    assert data.opening_balance == Decimal("0.00")
    assert data.parent_account_id is None


def test_account_create_invalid_chart_id():
    """Test validácie chart_id > 0."""
    with pytest.raises(ValueError, match="greater than 0"):
        AccountCreate(
            chart_id=0,
            account_number="111",
            name="Test",
            account_type_id=1,
            currency_code="EUR",
            level=1,
        )


def test_account_create_invalid_currency_code():
    """Test validácie currency_code dĺžky."""
    with pytest.raises(ValueError):
        AccountCreate(
            chart_id=1,
            account_number="111",
            name="Test",
            account_type_id=1,
            currency_code="EURO",  # > 3 znaky
            level=1,
        )


def test_account_create_invalid_level():
    """Test validácie level rozsahu (0-10)."""
    with pytest.raises(ValueError):
        AccountCreate(
            chart_id=1,
            account_number="111",
            name="Test",
            account_type_id=1,
            currency_code="EUR",
            level=11,  # > 10
        )


def test_account_create_with_parent():
    """Test vytvorenia AccountCreate s parent_account_id."""
    data = AccountCreate(
        chart_id=1,
        account_number="111.01",
        name="Sub-account",
        account_type_id=1,
        currency_code="EUR",
        parent_account_id=5,
        level=1,
    )
    assert data.parent_account_id == 5
    assert data.level == 1


def test_account_read_from_orm():
    """Test ORM mode v AccountRead."""

    class FakeORM:
        account_id = 1
        chart_id = 1
        account_number = "111"
        name = "Hotovosť"
        account_type_id = 1
        currency_code = "EUR"
        parent_account_id = None
        level = 0
        is_active = True
        opening_balance = Decimal("1000.00")
        current_balance = Decimal("1500.00")
        updated_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

    orm_obj = FakeORM()
    data = AccountRead.model_validate(orm_obj)
    assert data.account_id == 1
    assert data.account_number == "111"
    assert data.name == "Hotovosť"
    assert data.opening_balance == Decimal("1000.00")
    assert data.current_balance == Decimal("1500.00")
    assert data.updated_at == datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_account_update_partial():
    """Test partial update v AccountUpdate."""
    data = AccountUpdate(name="Nový názov")
    assert data.name == "Nový názov"
    assert data.is_active is None
    assert data.account_type_id is None


def test_account_update_invalid_level():
    """Test validácie level v AccountUpdate."""
    with pytest.raises(ValueError):
        AccountUpdate(level=-1)
