"""Tests for DocumentEntryLink model.

Covers:
- Basic CRUD (create link between source_document and journal_entry)
- UNIQUE constraint on (document_id, entry_id) — duplicate must raise
- CASCADE delete when source_document is deleted
- CASCADE delete when journal_entry is deleted
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
from app.models.document_entry_link import DocumentEntryLink
from app.models.import_batch import ImportBatch
from app.models.journal_entry import JournalEntry
from app.models.source_document import SourceDocument


def _create_dependencies(session, *, doc_suffix: str = "001", entry_suffix: str = "001"):
    """Create all FK dependencies required by DocumentEntryLink.

    Returns:
        Tuple of (source_document, journal_entry) instances persisted in session.
    """
    # Currency (required by SourceDocument)
    currency = Currency(
        currency_code="EUR",
        name="Euro",
        symbol="€",
    )
    session.add(currency)
    session.flush()

    # BusinessPartner (required by SourceDocument)
    partner = BusinessPartner(
        partner_type="SUPPLIER",
        code=f"SUP-{doc_suffix}",
        name="Test Supplier s.r.o.",
    )
    session.add(partner)
    session.flush()

    # ImportBatch (required by JournalEntry, optional but let's keep it consistent)
    batch = ImportBatch(
        filename="test_import.xlsx",
        file_hash=f"abc123hash{entry_suffix}",
        status="imported",
    )
    session.add(batch)
    session.flush()

    # SourceDocument
    doc = SourceDocument(
        document_type="received_invoice",
        document_number=f"FV-2025-{doc_suffix}",
        issue_date=datetime.date(2025, 6, 15),
        partner_id=partner.partner_id,
        total_amount=Decimal("1234.56"),
        currency_code=currency.currency_code,
    )
    session.add(doc)
    session.flush()

    # JournalEntry
    entry = JournalEntry(
        batch_id=batch.batch_id,
        entry_number=f"JE-2025-{entry_suffix}",
        entry_date=datetime.date(2025, 6, 15),
        description="Test journal entry",
    )
    session.add(entry)
    session.flush()

    return doc, entry


def test_create_link(db_session) -> None:
    """Test creating a link between source_document and journal_entry."""
    doc, entry = _create_dependencies(db_session)

    link = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()

    assert link.link_id is not None
    assert link.document_id == doc.document_id
    assert link.entry_id == entry.entry_id


def test_unique_constraint(db_session) -> None:
    """Test UNIQUE constraint on (document_id, entry_id) — duplicate must raise."""
    doc, entry = _create_dependencies(db_session)

    link1 = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link1)
    db_session.flush()

    link2 = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,  # same pair
    )
    db_session.add(link2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.flush()


def test_cascade_delete_document(db_session) -> None:
    """Test CASCADE delete — deleting source_document removes the link."""
    doc, entry = _create_dependencies(db_session)

    link = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()
    link_id = link.link_id

    # Delete source_document via raw SQL (CASCADE should remove link)
    db_session.execute(
        text("DELETE FROM source_document WHERE document_id = :id"),
        {"id": doc.document_id},
    )
    db_session.flush()

    # Verify link is gone
    result = db_session.execute(
        text("SELECT COUNT(*) FROM document_entry_link WHERE link_id = :id"),
        {"id": link_id},
    )
    count = result.scalar()
    assert count == 0


def test_cascade_delete_entry(db_session) -> None:
    """Test CASCADE delete — deleting journal_entry removes the link."""
    doc, entry = _create_dependencies(db_session)

    link = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()
    link_id = link.link_id

    # Delete journal_entry via raw SQL (CASCADE should remove link)
    db_session.execute(
        text("DELETE FROM journal_entry WHERE entry_id = :id"),
        {"id": entry.entry_id},
    )
    db_session.flush()

    # Verify link is gone
    result = db_session.execute(
        text("SELECT COUNT(*) FROM document_entry_link WHERE link_id = :id"),
        {"id": link_id},
    )
    count = result.scalar()
    assert count == 0


def test_server_default_created_at(db_session) -> None:
    """Test created_at is auto-populated by server default (not set explicitly)."""
    doc, entry = _create_dependencies(db_session)

    link = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()

    # Expire to force reload from DB (server_default)
    db_session.expire(link)

    assert link.created_at is not None
    assert isinstance(link.created_at, datetime.datetime)


def test_repr(db_session) -> None:
    """Test __repr__ includes link_id, document_id, and entry_id."""
    doc, entry = _create_dependencies(db_session)

    link = DocumentEntryLink(
        document_id=doc.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()

    repr_str = repr(link)
    assert "DocumentEntryLink" in repr_str
    assert str(link.link_id) in repr_str
    assert str(link.document_id) in repr_str
    assert str(link.entry_id) in repr_str
