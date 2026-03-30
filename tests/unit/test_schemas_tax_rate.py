"""Unit testy pre TaxRate Pydantic schemas."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.tax_rate import TaxRateCreate, TaxRateRead, TaxRateUpdate


def test_tax_rate_create_valid():
    """Test vytvorenia TaxRateCreate s validnymi datami."""
    tax_rate = TaxRateCreate(
        code="VAT_20",
        name="DPH 20%",
        rate=Decimal("20.0000"),
        valid_from=date(2024, 1, 1),
        valid_to=None,
        is_active=True,
    )
    assert tax_rate.code == "VAT_20"
    assert tax_rate.name == "DPH 20%"
    assert tax_rate.rate == Decimal("20.0000")
    assert tax_rate.valid_from == date(2024, 1, 1)
    assert tax_rate.valid_to is None
    assert tax_rate.is_active is True


def test_tax_rate_create_minimal():
    """Test vytvorenia TaxRateCreate s minimalnymi povinnymi polami."""
    tax_rate = TaxRateCreate(code="VAT_10", name="DPH 10%", rate=Decimal("10.5"))
    assert tax_rate.code == "VAT_10"
    assert tax_rate.name == "DPH 10%"
    assert tax_rate.rate == Decimal("10.5")
    assert tax_rate.valid_from is None
    assert tax_rate.valid_to is None
    assert tax_rate.is_active is True  # default


def test_tax_rate_create_code_max_length():
    """Test validacie max dlzky code (20 znakov)."""
    with pytest.raises(ValidationError) as exc_info:
        TaxRateCreate(
            code="A" * 21,  # 21 znakov — porusuje max_length=20
            name="Test",
            rate=Decimal("15.0"),
        )
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("code",) and "at most 20 characters" in e["msg"]
        for e in errors
    )


def test_tax_rate_create_rate_range():
    """Test validacie rate rozsahu (0-100)."""
    # Negativna sadzba
    with pytest.raises(ValidationError) as exc_info:
        TaxRateCreate(code="INVALID", name="Test", rate=Decimal("-1.0"))
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("rate",) and "greater than or equal to 0" in e["msg"]
        for e in errors
    )

    # Sadzba > 100%
    with pytest.raises(ValidationError) as exc_info:
        TaxRateCreate(code="INVALID", name="Test", rate=Decimal("101.0"))
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("rate",) and "less than or equal to 100" in e["msg"]
        for e in errors
    )


def test_tax_rate_create_rate_decimal_places():
    """Test validacie max 4 desatinne miesta pre rate."""
    # 4 desatinne miesta — OK
    tax_rate = TaxRateCreate(
        code="VAT_19", name="DPH 19.25%", rate=Decimal("19.2500")
    )
    assert tax_rate.rate == Decimal("19.2500")

    # 5 desatinnych miest — validacia zlyha
    with pytest.raises(ValidationError) as exc_info:
        TaxRateCreate(code="INVALID", name="Test", rate=Decimal("19.25001"))
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("rate",) for e in errors)


def test_tax_rate_read_orm_mode():
    """Test TaxRateRead ORM mode (from_attributes=True)."""

    # Simulacia ORM objektu
    class FakeORMTaxRate:
        tax_rate_id = 1
        code = "VAT_20"
        name = "DPH 20%"
        rate = Decimal("20.0000")
        valid_from = date(2024, 1, 1)
        valid_to = None
        is_active = True

    tax_rate = TaxRateRead.model_validate(FakeORMTaxRate())
    assert tax_rate.tax_rate_id == 1
    assert tax_rate.code == "VAT_20"
    assert tax_rate.rate == Decimal("20.0000")


def test_tax_rate_update_optional_fields():
    """Test TaxRateUpdate s partial update (len rate)."""
    tax_rate = TaxRateUpdate(rate=Decimal("15.0000"))
    assert tax_rate.rate == Decimal("15.0000")
    assert tax_rate.code is None
    assert tax_rate.name is None
    assert tax_rate.valid_from is None
    assert tax_rate.valid_to is None
    assert tax_rate.is_active is None


def test_tax_rate_update_validation():
    """Test validacie TaxRateUpdate (rovnake constrainty ako Create)."""
    with pytest.raises(ValidationError) as exc_info:
        TaxRateUpdate(code="A" * 21)  # max_length=20
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("code",) for e in errors)

    with pytest.raises(ValidationError) as exc_info:
        TaxRateUpdate(rate=Decimal("101.0"))  # max 100
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("rate",) for e in errors)
