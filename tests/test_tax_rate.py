"""Tests for TaxRate model constraints."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models import TaxRate


def test_insert_tax_rates(db_session):
    """Insert typical VAT rates."""
    vat_20 = TaxRate(
        code="VAT_20",
        name="DPH 20%",
        rate_percent=20.00,
        valid_from=date(2020, 1, 1),
    )
    vat_21 = TaxRate(
        code="VAT_21",
        name="DPH 21%",
        rate_percent=21.00,
        valid_from=date(2024, 1, 1),
    )
    vat_10 = TaxRate(
        code="VAT_10",
        name="DPH 10% (znížená)",
        rate_percent=10.00,
        valid_from=date(2020, 1, 1),
    )
    vat_0 = TaxRate(
        code="VAT_0",
        name="Oslobodené od DPH",
        rate_percent=0.00,
        valid_from=date(2020, 1, 1),
    )

    db_session.add_all([vat_20, vat_21, vat_10, vat_0])
    db_session.commit()

    assert db_session.query(TaxRate).count() == 4

    # Verify VAT_20 details
    loaded = db_session.query(TaxRate).filter_by(code="VAT_20").first()
    assert loaded.name == "DPH 20%"
    assert float(loaded.rate_percent) == 20.00
    assert loaded.valid_from == date(2020, 1, 1)
    assert loaded.valid_to is None
    assert loaded.is_active is True
    assert loaded.id is not None
    assert loaded.created_at is not None
    assert loaded.updated_at is not None


def test_unique_code_constraint(db_session):
    """Verify UNIQUE constraint on code."""
    vat1 = TaxRate(
        code="VAT_20",
        name="DPH 20%",
        rate_percent=20.00,
        valid_from=date(2020, 1, 1),
    )
    db_session.add(vat1)
    db_session.commit()

    vat2 = TaxRate(
        code="VAT_20",
        name="Duplicate",
        rate_percent=20.00,
        valid_from=date(2021, 1, 1),
    )
    db_session.add(vat2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "unique" in error_msg or "duplicate key" in error_msg
    db_session.rollback()


def test_rate_percent_check_constraint_negative(db_session):
    """Verify CHECK constraint rejects negative rate_percent."""
    invalid_rate = TaxRate(
        code="INVALID_NEG",
        name="Invalid Negative",
        rate_percent=-1.00,
        valid_from=date(2020, 1, 1),
    )
    db_session.add(invalid_rate)

    # pg8000 maps CHECK violations (23514) to ProgrammingError, not IntegrityError
    with pytest.raises((IntegrityError, ProgrammingError)) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "check" in error_msg or "tax_rate_percent_range" in error_msg
    db_session.rollback()


def test_rate_percent_check_constraint_over_100(db_session):
    """Verify CHECK constraint rejects rate_percent > 100."""
    invalid_rate = TaxRate(
        code="INVALID_HIGH",
        name="Invalid High",
        rate_percent=101.00,
        valid_from=date(2020, 1, 1),
    )
    db_session.add(invalid_rate)

    # pg8000 maps CHECK violations (23514) to ProgrammingError, not IntegrityError
    with pytest.raises((IntegrityError, ProgrammingError)) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "check" in error_msg or "tax_rate_percent_range" in error_msg
    db_session.rollback()


def test_is_active_default(db_session):
    """Verify is_active defaults to true."""
    rate = TaxRate(
        code="VAT_DEFAULT",
        name="Default Active",
        rate_percent=20.00,
        valid_from=date(2020, 1, 1),
    )
    db_session.add(rate)
    db_session.commit()

    # Refresh from DB to get server default
    db_session.refresh(rate)
    assert rate.is_active is True
