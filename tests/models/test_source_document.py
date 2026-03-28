"""Tests for SourceDocument model.

Covers:
- Basic CRUD (create, read)
- UNIQUE constraint on document_number
- FK RESTRICT behavior (partner_id, currency_code)
- Server default for created_at
- __repr__ output
"""

import datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.business_partner import BusinessPartner
from app.models.currency import Currency
from app.models.source_document import SourceDocument


def _create_dependencies(session) -> tuple[BusinessPartner, Currency]:
    """Create FK dependencies required by SourceDocument.

    Returns:
        Tuple of (partner, currency) instances persisted in session.
    """
    currency = Currency(
        currency_code="EUR",
        name="Euro",
        symbol="€",
    )
    session.add(currency)
    session.flush()

    partner = BusinessPartner(
        partner_type="SUPPLIER",
        code="SUP001",
        name="Test Supplier s.r.o.",
    )
    session.add(partner)
    session.flush()

    return partner, currency


def test_create_source_document(db_session) -> None:
    """Test creating a source document with all required fields."""
    partner, currency = _create_dependencies(db_session)

    doc = SourceDocument(
        document_type="received_invoice",
        document_number="FV-2025-001",
        issue_date=datetime.date(2025, 6, 15),
        partner_id=partner.partner_id,
        total_amount=Decimal("1234.56"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc)
    db_session.flush()

    assert doc.document_id is not None
    assert doc.document_type == "received_invoice"
    assert doc.document_number == "FV-2025-001"
    assert doc.issue_date == datetime.date(2025, 6, 15)
    assert doc.partner_id == partner.partner_id
    assert doc.total_amount == Decimal("1234.56")
    assert doc.currency_code == "EUR"


def test_unique_document_number(db_session) -> None:
    """Test UNIQUE constraint on document_number — duplicate must raise."""
    partner, currency = _create_dependencies(db_session)

    doc1 = SourceDocument(
        document_type="issued_invoice",
        document_number="FV-2025-DUP",
        issue_date=datetime.date(2025, 1, 10),
        partner_id=partner.partner_id,
        total_amount=Decimal("100.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc1)
    db_session.flush()

    doc2 = SourceDocument(
        document_type="received_invoice",
        document_number="FV-2025-DUP",  # same document_number
        issue_date=datetime.date(2025, 2, 20),
        partner_id=partner.partner_id,
        total_amount=Decimal("200.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.flush()


def test_fk_restrict_partner(db_session) -> None:
    """Test RESTRICT FK on partner deletion — must raise when document exists."""
    partner, currency = _create_dependencies(db_session)

    doc = SourceDocument(
        document_type="cash_receipt",
        document_number="PPD-2025-001",
        issue_date=datetime.date(2025, 3, 1),
        partner_id=partner.partner_id,
        total_amount=Decimal("50.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc)
    db_session.flush()

    # Use raw SQL for RESTRICT FK test — ORM delete sets FK to NULL first
    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text("DELETE FROM business_partner WHERE partner_id = :id"),
            {"id": partner.partner_id},
        )
        db_session.flush()


def test_fk_restrict_currency(db_session) -> None:
    """Test RESTRICT FK on currency deletion — must raise when document exists."""
    partner, currency = _create_dependencies(db_session)

    doc = SourceDocument(
        document_type="issued_invoice",
        document_number="FV-2025-CUR",
        issue_date=datetime.date(2025, 4, 15),
        partner_id=partner.partner_id,
        total_amount=Decimal("999.99"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc)
    db_session.flush()

    # Use raw SQL for RESTRICT FK test
    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text("DELETE FROM currency WHERE currency_code = :code"),
            {"code": currency.currency_code},
        )
        db_session.flush()


def test_server_default_created_at(db_session) -> None:
    """Test created_at is auto-populated by server default (not set explicitly)."""
    partner, currency = _create_dependencies(db_session)

    doc = SourceDocument(
        document_type="received_invoice",
        document_number="FV-2025-TS",
        issue_date=datetime.date(2025, 5, 1),
        partner_id=partner.partner_id,
        total_amount=Decimal("500.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc)
    db_session.flush()

    # Expire to force reload from DB (server_default)
    db_session.expire(doc)

    assert doc.created_at is not None
    assert isinstance(doc.created_at, datetime.datetime)


def test_repr(db_session) -> None:
    """Test __repr__ includes document_id, document_number, and document_type."""
    partner, currency = _create_dependencies(db_session)

    doc = SourceDocument(
        document_type="cash_receipt",
        document_number="PPD-2025-REP",
        issue_date=datetime.date(2025, 7, 1),
        partner_id=partner.partner_id,
        total_amount=Decimal("75.00"),
        currency_code=currency.currency_code,
    )
    db_session.add(doc)
    db_session.flush()

    repr_str = repr(doc)
    assert "SourceDocument" in repr_str
    assert str(doc.document_id) in repr_str
    assert "PPD-2025-REP" in repr_str
    assert "cash_receipt" in repr_str
