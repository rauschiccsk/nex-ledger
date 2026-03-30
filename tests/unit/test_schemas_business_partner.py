"""Unit testy pre BusinessPartner Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.business_partner import (
    BusinessPartnerCreate,
    BusinessPartnerRead,
    BusinessPartnerUpdate,
)


def test_business_partner_create_valid():
    """Test vytvorenia business partnera s validnými dátami."""
    partner = BusinessPartnerCreate(
        partner_type="customer",
        code="CUST001",
        name="Test Customer s.r.o.",
        tax_id="12345678",
        vat_number="SK2020123456",
        address="Bratislava, Slovensko",
        contact_person="Ján Novák",
        email="jan@test.sk",
        phone="+421900123456",
        is_active=True,
    )
    assert partner.partner_type == "customer"
    assert partner.code == "CUST001"
    assert partner.name == "Test Customer s.r.o."
    assert partner.tax_id == "12345678"
    assert partner.vat_number == "SK2020123456"


def test_business_partner_create_minimal():
    """Test vytvorenia partnera s minimálnymi povinnými poliami."""
    partner = BusinessPartnerCreate(
        partner_type="supplier",
        name="Minimal Supplier",
    )
    assert partner.partner_type == "supplier"
    assert partner.name == "Minimal Supplier"
    assert partner.code is None
    assert partner.tax_id is None
    assert partner.is_active is True  # default hodnota


def test_business_partner_create_invalid_partner_type():
    """Test validácie partner_type — musí byť customer/supplier/both."""
    with pytest.raises(ValidationError) as exc_info:
        BusinessPartnerCreate(
            partner_type="invalid",
            name="Test",
        )
    assert "partner_type" in str(exc_info.value)


def test_business_partner_create_invalid_email():
    """Test validácie emailu."""
    with pytest.raises(ValidationError) as exc_info:
        BusinessPartnerCreate(
            partner_type="customer",
            name="Test",
            email="invalid-email",
        )
    assert "email" in str(exc_info.value).lower()


def test_business_partner_read_from_orm():
    """Test čítania partnera z ORM objektu."""

    # Mock ORM objekt
    class MockPartner:
        partner_id = 1
        partner_type = "both"
        code = "BOTH001"
        name = "Both Partner"
        tax_id = "87654321"
        vat_number = "SK2020987654"
        address = "Košice"
        contact_person = "Peter Veľký"
        email = "peter@both.sk"
        phone = "0905555555"
        is_active = True

    partner = BusinessPartnerRead.model_validate(MockPartner())
    assert partner.partner_id == 1
    assert partner.partner_type == "both"
    assert partner.code == "BOTH001"


def test_business_partner_update_partial():
    """Test partial update — všetky polia optional."""
    update = BusinessPartnerUpdate(
        name="Updated Name",
        is_active=False,
    )
    assert update.name == "Updated Name"
    assert update.is_active is False
    assert update.partner_type is None
    assert update.code is None


def test_business_partner_update_all_none():
    """Test update s prázdnym telom."""
    update = BusinessPartnerUpdate()
    assert update.partner_type is None
    assert update.name is None
    assert update.is_active is None


def test_business_partner_update_invalid_email():
    """Test validácie emailu pri update."""
    with pytest.raises(ValidationError) as exc_info:
        BusinessPartnerUpdate(
            email="bad-email",
        )
    assert "email" in str(exc_info.value).lower()
