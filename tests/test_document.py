"""Tests for the Document model."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.document import Document, DocumentType
from app.models.journal_entry import EntryStatus, JournalEntry


def test_create_invoice(db_session, sample_business_partner):
    """Test creating an invoice document."""
    doc = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        due_date=date(2024, 2, 15),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("1500.00"),
        description="Software development services",
        file_path="/documents/2024/INV-2024-001.pdf",
    )
    db_session.add(doc)
    db_session.commit()

    assert doc.id is not None
    assert doc.document_type == DocumentType.INVOICE
    assert doc.amount == Decimal("1500.00")
    assert doc.due_date == date(2024, 2, 15)
    assert doc.description == "Software development services"
    assert doc.file_path == "/documents/2024/INV-2024-001.pdf"


def test_create_receipt(db_session, sample_business_partner):
    """Test creating a receipt document."""
    doc = Document(
        document_number="REC-2024-001",
        document_type=DocumentType.RECEIPT,
        document_date=date(2024, 1, 20),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("1500.00"),
    )
    db_session.add(doc)
    db_session.commit()

    assert doc.document_type == DocumentType.RECEIPT
    assert doc.due_date is None  # Receipts typically don't have due dates


def test_unique_document_number(db_session, sample_business_partner):
    """Test UNIQUE constraint on document_number."""
    doc1 = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("1000.00"),
    )
    db_session.add(doc1)
    db_session.commit()

    doc2 = Document(
        document_number="INV-2024-001",  # Duplicate
        document_type=DocumentType.RECEIPT,
        document_date=date(2024, 1, 20),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("500.00"),
    )
    db_session.add(doc2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_check_document_type_enum(db_session, sample_business_partner):
    """Test CHECK constraint on document_type (via ENUM)."""
    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text(
                "INSERT INTO document"
                " (id, document_number, document_type, document_date,"
                "  business_partner_id, amount)"
                " VALUES (gen_random_uuid(), 'TEST-001', 'invalid_type',"
                "  '2024-01-15', :bp_id, 1000.00)"
            ),
            {"bp_id": str(sample_business_partner.id)},
        )


def test_fk_business_partner_restrict(db_session, sample_business_partner):
    """Test FK RESTRICT on business_partner deletion.

    Must use raw SQL — ORM session.delete() sets FK to NULL first,
    which hits NOT NULL before FK check (pg8000 quirk).
    """
    doc = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("1000.00"),
    )
    db_session.add(doc)
    db_session.commit()

    # Try to delete business partner via raw SQL (should fail with FK RESTRICT)
    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.execute(
            text("DELETE FROM business_partner WHERE id = :id"),
            {"id": str(sample_business_partner.id)},
        )


def test_fk_journal_entry_set_null(db_session, sample_business_partner):
    """Test FK SET NULL on journal_entry deletion."""
    entry = JournalEntry(
        entry_number="JE-001",
        entry_date=date(2024, 1, 15),
        description="Invoice journal entry",
        status=EntryStatus.DRAFT,
    )
    db_session.add(entry)
    db_session.commit()

    doc = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        business_partner_id=sample_business_partner.id,
        journal_entry_id=entry.id,
        amount=Decimal("1000.00"),
    )
    db_session.add(doc)
    db_session.commit()

    # Delete journal entry — FK SET NULL should set doc.journal_entry_id to NULL
    db_session.execute(
        text("DELETE FROM journal_entry WHERE id = :id"),
        {"id": str(entry.id)},
    )
    db_session.commit()

    # Document should still exist, journal_entry_id set to NULL
    db_session.expire(doc)
    assert doc.journal_entry_id is None


def test_document_relationships(db_session, sample_business_partner):
    """Test bidirectional relationships."""
    doc = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("1000.00"),
    )
    db_session.add(doc)
    db_session.commit()

    # Test Document -> BusinessPartner
    assert doc.business_partner.id == sample_business_partner.id

    # Test BusinessPartner -> Documents
    db_session.expire(sample_business_partner)
    assert len(sample_business_partner.documents) == 1
    assert sample_business_partner.documents[0].document_number == "INV-2024-001"


def test_document_with_journal_entry(db_session, sample_business_partner):
    """Test document linked to journal entry."""
    entry = JournalEntry(
        entry_number="JE-001",
        entry_date=date(2024, 1, 15),
        description="Invoice journal entry",
        status=EntryStatus.DRAFT,
    )
    db_session.add(entry)
    db_session.commit()

    doc = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        business_partner_id=sample_business_partner.id,
        journal_entry_id=entry.id,
        amount=Decimal("1000.00"),
    )
    db_session.add(doc)
    db_session.commit()

    # Test Document -> JournalEntry
    assert doc.journal_entry.entry_number == "JE-001"

    # Test JournalEntry -> Documents
    db_session.expire(entry)
    assert len(entry.documents) == 1
    assert entry.documents[0].document_number == "INV-2024-001"


def test_document_repr(db_session, sample_business_partner):
    """Test __repr__ method."""
    doc = Document(
        document_number="INV-2024-001",
        document_type=DocumentType.INVOICE,
        document_date=date(2024, 1, 15),
        business_partner_id=sample_business_partner.id,
        amount=Decimal("1234.56"),
    )
    db_session.add(doc)
    db_session.commit()

    assert "INV-2024-001" in repr(doc)
    assert "1234.56" in repr(doc)
