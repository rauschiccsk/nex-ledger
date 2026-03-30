"""Unit testy pre SourceDocument Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.schemas.source_document import (
    SourceDocumentCreate,
    SourceDocumentRead,
    SourceDocumentUpdate,
)


def test_source_document_create_valid():
    """Test vytvorenia SourceDocument s validnými dátami."""
    data = {
        "document_type": "invoice",
        "document_number": "INV-2024-001",
        "issue_date": date(2024, 1, 15),
        "partner_id": 1,
        "total_amount": Decimal("1500.50"),
        "currency_code": "EUR",
    }
    schema = SourceDocumentCreate(**data)
    assert schema.document_type == "invoice"
    assert schema.document_number == "INV-2024-001"
    assert schema.total_amount == Decimal("1500.50")


def test_source_document_create_document_type_validation():
    """Test validácie document_type enum."""
    with pytest.raises(ValueError):
        SourceDocumentCreate(
            document_type="invalid_type",
            document_number="INV-001",
            issue_date=date(2024, 1, 1),
            partner_id=1,
            total_amount=Decimal("100.00"),
            currency_code="EUR",
        )


def test_source_document_create_negative_amount():
    """Test negatívnej sumy (neprípustné)."""
    with pytest.raises(ValueError):
        SourceDocumentCreate(
            document_type="invoice",
            document_number="INV-001",
            issue_date=date(2024, 1, 1),
            partner_id=1,
            total_amount=Decimal("-100.00"),
            currency_code="EUR",
        )


def test_source_document_create_invalid_partner_id():
    """Test neplatného partner_id (musí byť > 0)."""
    with pytest.raises(ValueError):
        SourceDocumentCreate(
            document_type="invoice",
            document_number="INV-001",
            issue_date=date(2024, 1, 1),
            partner_id=0,
            total_amount=Decimal("100.00"),
            currency_code="EUR",
        )


def test_source_document_create_invalid_currency_code():
    """Test neplatného currency_code (musí byť presne 3 znaky)."""
    with pytest.raises(ValueError):
        SourceDocumentCreate(
            document_type="invoice",
            document_number="INV-001",
            issue_date=date(2024, 1, 1),
            partner_id=1,
            total_amount=Decimal("100.00"),
            currency_code="EU",  # len 2 znaky
        )


def test_source_document_read_from_orm():
    """Test ORM mode (from_attributes=True)."""

    class MockSourceDocument:
        document_id = 1
        document_type = "received_invoice"
        document_number = "RINV-2024-001"
        issue_date = date(2024, 1, 20)
        partner_id = 5
        total_amount = Decimal("2500.75")
        currency_code = "USD"
        created_at = datetime(2024, 1, 20, 10, 30, 0)

    mock = MockSourceDocument()
    schema = SourceDocumentRead.model_validate(mock)
    assert schema.document_id == 1
    assert schema.document_type == "received_invoice"
    assert schema.total_amount == Decimal("2500.75")


def test_source_document_update_partial():
    """Test partial update — všetky polia optional."""
    schema = SourceDocumentUpdate(
        total_amount=Decimal("3000.00"), currency_code="GBP"
    )
    assert schema.total_amount == Decimal("3000.00")
    assert schema.currency_code == "GBP"
    assert schema.document_type is None


def test_source_document_update_document_type_validation():
    """Test validácie document_type v update."""
    with pytest.raises(ValueError):
        SourceDocumentUpdate(document_type="invalid_type")


def test_source_document_update_empty():
    """Test prázdneho update (všetky polia None)."""
    schema = SourceDocumentUpdate()
    assert schema.document_type is None
    assert schema.document_number is None
    assert schema.total_amount is None
