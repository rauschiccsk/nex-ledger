"""Tests for BusinessPartner model."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.business_partner import BusinessPartner


def test_create_business_partner_customer(db_session):
    """Test creating a customer business partner."""
    partner = BusinessPartner(
        code="CUST001",
        name="ACME Corp",
        tax_id="SK2021234567",
        vat_id="SK2021234567",
        street="Main Street 123",
        city="Bratislava",
        postal_code="81101",
        country_code="SK",
        email="info@acme.sk",
        phone="+421901234567",
        is_customer=True,
        is_supplier=False,
    )
    db_session.add(partner)
    db_session.commit()

    result = db_session.execute(
        select(BusinessPartner).where(BusinessPartner.code == "CUST001")
    ).scalar_one()

    assert result.name == "ACME Corp"
    assert result.is_customer is True
    assert result.is_supplier is False
    assert result.is_active is True  # default
    assert result.id is not None
    assert result.created_at is not None


def test_create_business_partner_supplier(db_session):
    """Test creating a supplier business partner."""
    partner = BusinessPartner(
        code="SUPP001",
        name="Parts Inc",
        tax_id="SK2098765432",
        is_customer=False,
        is_supplier=True,
    )
    db_session.add(partner)
    db_session.commit()

    result = db_session.execute(
        select(BusinessPartner).where(BusinessPartner.code == "SUPP001")
    ).scalar_one()

    assert result.name == "Parts Inc"
    assert result.is_customer is False
    assert result.is_supplier is True


def test_business_partner_code_unique(db_session):
    """Test UNIQUE constraint on code."""
    partner1 = BusinessPartner(code="BP001", name="First Partner", is_customer=True)
    db_session.add(partner1)
    db_session.commit()

    partner2 = BusinessPartner(code="BP001", name="Duplicate Code", is_customer=True)
    db_session.add(partner2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_business_partner_minimal_fields(db_session):
    """Test business partner with only required fields."""
    partner = BusinessPartner(code="MIN001", name="Minimal Partner")
    db_session.add(partner)
    db_session.commit()

    result = db_session.execute(
        select(BusinessPartner).where(BusinessPartner.code == "MIN001")
    ).scalar_one()

    assert result.name == "Minimal Partner"
    assert result.tax_id is None
    assert result.email is None
    assert result.is_customer is False  # server default
    assert result.is_supplier is False  # server default
    assert result.is_active is True  # server default


def test_business_partner_both_customer_and_supplier(db_session):
    """Test business partner that is both customer and supplier."""
    partner = BusinessPartner(
        code="BOTH001",
        name="Multi-Role Partner",
        is_customer=True,
        is_supplier=True,
    )
    db_session.add(partner)
    db_session.commit()

    result = db_session.execute(
        select(BusinessPartner).where(BusinessPartner.code == "BOTH001")
    ).scalar_one()

    assert result.is_customer is True
    assert result.is_supplier is True


def test_business_partner_repr(db_session):
    """Test string representation."""
    partner = BusinessPartner(code="REPR001", name="Repr Test")
    assert "REPR001" in repr(partner)
    assert "Repr Test" in repr(partner)


def test_business_partner_inactive(db_session):
    """Test inactive business partner."""
    partner = BusinessPartner(
        code="INACTIVE001",
        name="Inactive Partner",
        is_active=False,
    )
    db_session.add(partner)
    db_session.commit()

    result = db_session.execute(
        select(BusinessPartner).where(BusinessPartner.code == "INACTIVE001")
    ).scalar_one()

    assert result.is_active is False
