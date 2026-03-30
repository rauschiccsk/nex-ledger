"""Unit testy pre Currency Pydantic schémy."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.currency import CurrencyCreate, CurrencyRead, CurrencyUpdate


def test_currency_create_valid():
    """Test vytvorenia CurrencyCreate s platnými dátami."""
    data = {
        "currency_code": "USD",
        "name": "US Dollar",
        "symbol": "$",
        "decimal_places": 2,
        "is_active": True,
    }
    schema = CurrencyCreate(**data)
    assert schema.currency_code == "USD"
    assert schema.name == "US Dollar"
    assert schema.symbol == "$"
    assert schema.decimal_places == 2
    assert schema.is_active is True


def test_currency_create_minimal():
    """Test vytvorenia CurrencyCreate s minimálnymi povinnými poľami."""
    data = {
        "currency_code": "EUR",
        "name": "Euro",
        "decimal_places": 2,
    }
    schema = CurrencyCreate(**data)
    assert schema.currency_code == "EUR"
    assert schema.symbol is None
    assert schema.is_active is True  # default hodnota


def test_currency_create_invalid_code_length():
    """Test validácie max_length pre currency_code."""
    with pytest.raises(ValidationError) as exc_info:
        CurrencyCreate(
            currency_code="TOOLONG",
            name="Test",
            decimal_places=2,
        )
    errors = exc_info.value.errors()
    assert any("currency_code" in str(e) for e in errors)


def test_currency_create_invalid_decimal_places():
    """Test validácie decimal_places range (0-10)."""
    with pytest.raises(ValidationError):
        CurrencyCreate(
            currency_code="USD",
            name="US Dollar",
            decimal_places=-1,  # invalid
        )

    with pytest.raises(ValidationError):
        CurrencyCreate(
            currency_code="USD",
            name="US Dollar",
            decimal_places=11,  # invalid
        )


def test_currency_read_from_orm():
    """Test CurrencyRead from_attributes (ORM mode)."""

    class MockORM:
        currency_code = "GBP"
        name = "British Pound"
        symbol = "£"
        decimal_places = 2
        is_active = True
        updated_at = datetime(2026, 3, 30, 10, 0, 0)

    schema = CurrencyRead.model_validate(MockORM())
    assert schema.currency_code == "GBP"
    assert schema.name == "British Pound"
    assert schema.symbol == "£"
    assert schema.decimal_places == 2
    assert schema.is_active is True
    assert schema.updated_at == datetime(2026, 3, 30, 10, 0, 0)


def test_currency_update_all_fields_optional():
    """Test CurrencyUpdate s partial update (všetky polia optional)."""
    # Prázdny update je validný
    schema = CurrencyUpdate()
    assert schema.name is None
    assert schema.symbol is None
    assert schema.decimal_places is None
    assert schema.is_active is None

    # Partial update
    schema = CurrencyUpdate(name="Updated Name", is_active=False)
    assert schema.name == "Updated Name"
    assert schema.is_active is False
    assert schema.symbol is None  # ostatné polia nezmenené


def test_currency_update_validation():
    """Test validácie CurrencyUpdate polí."""
    with pytest.raises(ValidationError):
        CurrencyUpdate(decimal_places=-5)  # mimo rozsah

    with pytest.raises(ValidationError):
        CurrencyUpdate(name="x" * 101)  # max_length exceeded
