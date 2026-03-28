"""Tests for TaxRate model — constraints, defaults, and validation."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.tax_rate import TaxRate


def test_create_tax_rate(db_session):
    """Test creating tax rate with valid data."""
    tax_rate = TaxRate(
        code="VAT_20",
        name="DPH 20%",
        rate_percent=Decimal("20.00"),
        valid_from=date(2024, 1, 1),
    )
    db_session.add(tax_rate)
    db_session.commit()

    assert tax_rate.id is not None
    assert tax_rate.code == "VAT_20"
    assert tax_rate.rate_percent == Decimal("20.00")
    assert tax_rate.is_active is True


def test_tax_rate_unique_code(db_session):
    """Test UNIQUE constraint on code."""
    tax_rate1 = TaxRate(
        code="VAT_21",
        name="DPH 21%",
        rate_percent=Decimal("21.00"),
        valid_from=date(2025, 1, 1),
    )
    db_session.add(tax_rate1)
    db_session.commit()

    tax_rate2 = TaxRate(
        code="VAT_21",  # Duplicate
        name="DPH 21% (duplicate)",
        rate_percent=Decimal("21.00"),
        valid_from=date(2025, 1, 1),
    )
    db_session.add(tax_rate2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_tax_rate_check_negative(db_session):
    """Test CHECK constraint rejects negative rate."""
    tax_rate = TaxRate(
        code="INVALID_NEG",
        name="Invalid negative",
        rate_percent=Decimal("-1.00"),
        valid_from=date(2024, 1, 1),
    )
    db_session.add(tax_rate)

    # pg8000 maps CHECK violations (23514) to ProgrammingError, not IntegrityError
    with pytest.raises((IntegrityError, ProgrammingError), match="ck_tax_rate_percent"):
        db_session.commit()


def test_tax_rate_check_over_100(db_session):
    """Test CHECK constraint rejects rate > 100."""
    tax_rate = TaxRate(
        code="INVALID_HIGH",
        name="Invalid over 100",
        rate_percent=Decimal("101.00"),
        valid_from=date(2024, 1, 1),
    )
    db_session.add(tax_rate)

    # pg8000 maps CHECK violations (23514) to ProgrammingError, not IntegrityError
    with pytest.raises((IntegrityError, ProgrammingError), match="ck_tax_rate_percent"):
        db_session.commit()


def test_tax_rate_zero_percent(db_session):
    """Test 0% rate is valid."""
    tax_rate = TaxRate(
        code="VAT_0",
        name="DPH 0% (oslobodene)",
        rate_percent=Decimal("0.00"),
        valid_from=date(2024, 1, 1),
    )
    db_session.add(tax_rate)
    db_session.commit()

    assert tax_rate.rate_percent == Decimal("0.00")


def test_tax_rate_valid_to_optional(db_session):
    """Test valid_to is nullable."""
    tax_rate = TaxRate(
        code="VAT_CURRENT",
        name="Aktualna sadzba",
        rate_percent=Decimal("20.00"),
        valid_from=date(2024, 1, 1),
        valid_to=None,
    )
    db_session.add(tax_rate)
    db_session.commit()

    assert tax_rate.valid_to is None


def test_tax_rate_repr(db_session):
    """Test string representation."""
    tax_rate = TaxRate(
        code="VAT_TEST",
        name="Test rate",
        rate_percent=Decimal("15.50"),
        valid_from=date(2024, 1, 1),
    )
    repr_str = repr(tax_rate)
    assert "VAT_TEST" in repr_str
    assert "15.50" in repr_str
