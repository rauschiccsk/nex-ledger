"""Unit testy pre OpeningBalance Pydantic schemas."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.opening_balance import (
    OpeningBalanceCreate,
    OpeningBalanceRead,
    OpeningBalanceUpdate,
)


def test_opening_balance_create_valid():
    """Test vytvorenia OpeningBalance s validnými dátami."""
    data = {
        "period_id": 1,
        "account_id": 100,
        "debit_amount": Decimal("1500.00"),
        "credit_amount": Decimal("0.00"),
    }
    ob = OpeningBalanceCreate(**data)
    assert ob.period_id == 1
    assert ob.account_id == 100
    assert ob.debit_amount == Decimal("1500.00")
    assert ob.credit_amount == Decimal("0.00")


def test_opening_balance_create_defaults():
    """Test default hodnôt pre debit/credit amounts."""
    ob = OpeningBalanceCreate(period_id=1, account_id=100)
    assert ob.debit_amount == Decimal("0.00")
    assert ob.credit_amount == Decimal("0.00")


def test_opening_balance_create_invalid_fk():
    """Test validácie FK constraints (> 0)."""
    with pytest.raises(ValidationError) as exc_info:
        OpeningBalanceCreate(period_id=0, account_id=100)
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("period_id",) and "greater than 0" in e["msg"] for e in errors)

    with pytest.raises(ValidationError) as exc_info:
        OpeningBalanceCreate(period_id=1, account_id=-5)
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("account_id",) and "greater than 0" in e["msg"] for e in errors)


def test_opening_balance_create_negative_amounts():
    """Test validácie záporných súm (nepovolené)."""
    with pytest.raises(ValidationError) as exc_info:
        OpeningBalanceCreate(
            period_id=1, account_id=100, debit_amount=Decimal("-50.00")
        )
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("debit_amount",) and "greater than or equal to 0" in e["msg"]
        for e in errors
    )


def test_opening_balance_read_orm_mode():
    """Test ORM mode (from_attributes=True)."""

    class MockORM:
        balance_id = 42
        period_id = 1
        account_id = 100
        debit_amount = Decimal("1500.00")
        credit_amount = Decimal("0.00")
        created_at = datetime.now(UTC)

    ob = OpeningBalanceRead.model_validate(MockORM())
    assert ob.balance_id == 42
    assert ob.period_id == 1
    assert ob.account_id == 100
    assert ob.debit_amount == Decimal("1500.00")


def test_opening_balance_update_partial():
    """Test partial update (všetky polia optional)."""
    ob = OpeningBalanceUpdate(debit_amount=Decimal("2000.00"))
    assert ob.debit_amount == Decimal("2000.00")
    assert ob.credit_amount is None

    ob2 = OpeningBalanceUpdate(credit_amount=Decimal("500.00"))
    assert ob2.debit_amount is None
    assert ob2.credit_amount == Decimal("500.00")


def test_opening_balance_update_empty():
    """Test prázdneho update objektu."""
    ob = OpeningBalanceUpdate()
    assert ob.debit_amount is None
    assert ob.credit_amount is None


def test_opening_balance_update_invalid_amount():
    """Test validácie zápornej sumy v update."""
    with pytest.raises(ValidationError) as exc_info:
        OpeningBalanceUpdate(debit_amount=Decimal("-100.00"))
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("debit_amount",) and "greater than or equal to 0" in e["msg"]
        for e in errors
    )
