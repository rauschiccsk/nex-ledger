"""Tests for BusinessPartner model constraints and defaults."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import BusinessPartner


def test_insert_customer(db_session):
    """Test inserting a customer partner with full details."""
    partner = BusinessPartner(
        code="CUST001",
        name="Acme Corporation",
        tax_id="12345678",
        vat_id="SK12345678",
        street="Main Street 123",
        city="Bratislava",
        postal_code="811 01",
        country_code="SK",
        email="acme@example.com",
        phone="+421901123456",
        is_customer=True,
        is_supplier=False,
    )
    db_session.add(partner)
    db_session.commit()
    db_session.refresh(partner)

    assert partner.id is not None
    assert partner.code == "CUST001"
    assert partner.name == "Acme Corporation"
    assert partner.tax_id == "12345678"
    assert partner.vat_id == "SK12345678"
    assert partner.street == "Main Street 123"
    assert partner.city == "Bratislava"
    assert partner.postal_code == "811 01"
    assert partner.country_code == "SK"
    assert partner.email == "acme@example.com"
    assert partner.phone == "+421901123456"
    assert partner.is_customer is True
    assert partner.is_supplier is False
    assert partner.is_active is True  # default value
    assert partner.created_at is not None
    assert partner.updated_at is not None


def test_insert_supplier(db_session):
    """Test inserting a supplier partner with minimal fields."""
    partner = BusinessPartner(
        code="SUPP001",
        name="Supply Chain Inc.",
        tax_id="87654321",
        is_customer=False,
        is_supplier=True,
    )
    db_session.add(partner)
    db_session.commit()
    db_session.refresh(partner)

    assert partner.id is not None
    assert partner.code == "SUPP001"
    assert partner.name == "Supply Chain Inc."
    assert partner.is_customer is False
    assert partner.is_supplier is True
    assert partner.is_active is True  # default


def test_insert_customer_and_supplier(db_session):
    """Test inserting a partner with both customer and supplier roles."""
    partner = BusinessPartner(
        code="BOTH001",
        name="Universal Trading Ltd.",
        is_customer=True,
        is_supplier=True,
    )
    db_session.add(partner)
    db_session.commit()
    db_session.refresh(partner)

    assert partner.is_customer is True
    assert partner.is_supplier is True
    assert partner.is_active is True


def test_unique_code_constraint(db_session):
    """Test that duplicate code raises IntegrityError."""
    partner1 = BusinessPartner(code="DUP001", name="First Partner")
    db_session.add(partner1)
    db_session.commit()

    partner2 = BusinessPartner(code="DUP001", name="Second Partner")
    db_session.add(partner2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "unique" in error_msg or "duplicate key" in error_msg
    db_session.rollback()


def test_default_values(db_session):
    """Test default values for boolean flags."""
    partner = BusinessPartner(code="DEF001", name="Default Test")
    db_session.add(partner)
    db_session.commit()
    db_session.refresh(partner)

    assert partner.is_customer is False  # server_default='false'
    assert partner.is_supplier is False  # server_default='false'
    assert partner.is_active is True     # server_default='true'
    assert partner.created_at is not None
    assert partner.updated_at is not None
