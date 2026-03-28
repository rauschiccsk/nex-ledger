"""Tests for BusinessPartner model."""

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.business_partner import BusinessPartner


def test_create_customer_partner(db_session):
    """Test creating a customer business partner with all fields."""
    partner = BusinessPartner(
        partner_type="CUSTOMER",
        code="CUST001",
        name="Test Customer Ltd.",
        tax_id="12345678",
        vat_number="SK12345678",
        address="Bratislava, Slovakia",
        contact_person="Ján Novák",
        email="customer@example.com",
        phone="+421 900 123 456",
    )
    db_session.add(partner)
    db_session.commit()

    assert partner.partner_id is not None
    assert partner.partner_type == "CUSTOMER"
    assert partner.code == "CUST001"
    assert partner.name == "Test Customer Ltd."
    assert partner.tax_id == "12345678"
    assert partner.vat_number == "SK12345678"
    assert partner.address == "Bratislava, Slovakia"
    assert partner.contact_person == "Ján Novák"
    assert partner.email == "customer@example.com"
    assert partner.phone == "+421 900 123 456"
    assert partner.is_active is True


def test_create_supplier_partner(db_session):
    """Test creating a supplier business partner."""
    partner = BusinessPartner(
        partner_type="SUPPLIER",
        code="SUP001",
        name="Test Supplier s.r.o.",
        address="Košice, Slovakia",
    )
    db_session.add(partner)
    db_session.commit()

    assert partner.partner_id is not None
    assert partner.partner_type == "SUPPLIER"
    assert partner.code == "SUP001"


def test_create_both_type_partner(db_session):
    """Test creating a partner that is both customer and supplier."""
    partner = BusinessPartner(
        partner_type="BOTH",
        code="BOTH001",
        name="Hybrid Partner Inc.",
    )
    db_session.add(partner)
    db_session.commit()

    assert partner.partner_type == "BOTH"


def test_partner_type_check_constraint(db_session):
    """Test that invalid partner_type raises error (CHECK constraint)."""
    partner = BusinessPartner(
        partner_type="INVALID",
        code="INVALID001",
        name="Invalid Partner",
    )
    db_session.add(partner)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_unique_code_constraint(db_session):
    """Test that duplicate code raises IntegrityError."""
    partner1 = BusinessPartner(
        partner_type="CUSTOMER",
        code="DUP001",
        name="First Partner",
    )
    db_session.add(partner1)
    db_session.commit()

    partner2 = BusinessPartner(
        partner_type="SUPPLIER",
        code="DUP001",
        name="Second Partner",
    )
    db_session.add(partner2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_nullable_fields(db_session):
    """Test that optional fields default to NULL."""
    partner = BusinessPartner(
        partner_type="CUSTOMER",
        code="MIN001",
        name="Minimal Partner",
    )
    db_session.add(partner)
    db_session.commit()

    assert partner.tax_id is None
    assert partner.vat_number is None
    assert partner.address is None
    assert partner.contact_person is None
    assert partner.email is None
    assert partner.phone is None


def test_server_default_is_active(db_session):
    """Test that is_active defaults to TRUE via server_default."""
    partner = BusinessPartner(
        partner_type="CUSTOMER",
        code="DEF001",
        name="Default Active Partner",
    )
    db_session.add(partner)
    db_session.commit()

    # Refresh from DB to get server default
    db_session.refresh(partner)
    assert partner.is_active is True


def test_repr(db_session):
    """Test BusinessPartner __repr__ method."""
    partner = BusinessPartner(
        partner_type="CUSTOMER",
        code="REPR001",
        name="Repr Test Partner",
    )
    db_session.add(partner)
    db_session.commit()

    repr_str = repr(partner)
    assert "BusinessPartner" in repr_str
    assert "REPR001" in repr_str
    assert "Repr Test Partner" in repr_str
    assert "CUSTOMER" in repr_str
