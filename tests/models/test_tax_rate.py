"""Tests for TaxRate model."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.tax_rate import TaxRate


def test_create_tax_rate(db_session):
    """Test creating a VAT tax rate with all fields."""
    vat = TaxRate(
        code="VAT20",
        name="Value Added Tax 20%",
        rate=Decimal("20.00"),
        valid_from=date(2024, 1, 1),
        is_active=True,
    )
    db_session.add(vat)
    db_session.commit()

    assert vat.tax_rate_id is not None
    assert vat.code == "VAT20"
    assert vat.rate == Decimal("20.00")
    assert vat.valid_from == date(2024, 1, 1)
    assert vat.valid_to is None
    assert vat.is_active is True


def test_rate_check_constraint_above_100(db_session):
    """Test that rate > 100 raises error (CHECK constraint)."""
    invalid_rate = TaxRate(
        code="INVALID",
        name="Invalid Rate",
        rate=Decimal("150.00"),
    )
    db_session.add(invalid_rate)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_rate_check_constraint_negative(db_session):
    """Test that negative rate raises error (CHECK constraint)."""
    negative_rate = TaxRate(
        code="NEGATIVE",
        name="Negative Rate",
        rate=Decimal("-5.00"),
    )
    db_session.add(negative_rate)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_unique_code_constraint(db_session):
    """Test that duplicate code raises IntegrityError."""
    vat1 = TaxRate(code="VAT10", name="VAT 10%", rate=Decimal("10.00"))
    db_session.add(vat1)
    db_session.commit()

    vat2 = TaxRate(code="VAT10", name="Duplicate", rate=Decimal("15.00"))
    db_session.add(vat2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_nullable_dates(db_session):
    """Test that valid_from and valid_to can be NULL."""
    rate = TaxRate(
        code="NODATES",
        name="No Dates",
        rate=Decimal("5.00"),
    )
    db_session.add(rate)
    db_session.commit()

    assert rate.valid_from is None
    assert rate.valid_to is None


def test_default_is_active(db_session):
    """Test that is_active defaults to TRUE via server_default."""
    rate = TaxRate(
        code="DEFAULT",
        name="Default Active",
        rate=Decimal("8.00"),
    )
    db_session.add(rate)
    db_session.commit()

    # Refresh from DB to get server default
    db_session.expire(rate)
    assert rate.is_active is True


def test_repr(db_session):
    """Test __repr__ method."""
    rate = TaxRate(code="TEST", name="Test Rate", rate=Decimal("12.50"))
    assert repr(rate) == "<TaxRate(code='TEST', rate=12.50%)>"
