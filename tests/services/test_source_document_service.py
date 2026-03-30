"""
Tests for SourceDocumentService CRUD operations.

Covers: list_documents, get_document, create_document, update_document,
        delete_document.
14 tests in 5 classes.
"""

import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.business_partner import BusinessPartner
from app.models.currency import Currency
from app.models.document_entry_link import DocumentEntryLink
from app.models.import_batch import ImportBatch
from app.models.journal_entry import JournalEntry
from app.models.source_document import SourceDocument
from app.services.source_document_service import SourceDocumentService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def sample_currency(db_session: Session) -> Currency:
    """Create EUR currency required by SourceDocument FK."""
    c = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(c)
    db_session.flush()
    return c


@pytest.fixture()
def sample_partner(db_session: Session) -> BusinessPartner:
    """Create a business partner required by SourceDocument FK."""
    p = BusinessPartner(
        partner_type="CUSTOMER",
        code="DOC-CUST001",
        name="Doc Test Customer",
    )
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def doc_defaults(
    sample_currency: Currency, sample_partner: BusinessPartner
) -> dict:
    """Return default valid fields for SourceDocument creation."""
    return {
        "document_type": "issued_invoice",
        "document_number": "INV001",
        "issue_date": datetime.date(2026, 1, 15),
        "partner_id": sample_partner.partner_id,
        "total_amount": Decimal("1000.00"),
        "currency_code": "EUR",
    }


@pytest.fixture()
def document(
    db_session: Session, doc_defaults: dict
) -> SourceDocument:
    """Create a single source document."""
    doc = SourceDocument(**doc_defaults)
    db_session.add(doc)
    db_session.flush()
    return doc


@pytest.fixture()
def five_documents(
    db_session: Session, doc_defaults: dict
) -> list[SourceDocument]:
    """Create 5 source documents for pagination testing."""
    docs = []
    for i in range(1, 6):
        data = {**doc_defaults, "document_number": f"DOC{i:03d}"}
        doc = SourceDocument(**data)
        db_session.add(doc)
        db_session.flush()
        docs.append(doc)
    return docs


@pytest.fixture()
def document_with_entry_link(
    db_session: Session, document: SourceDocument
) -> DocumentEntryLink:
    """Create a DocumentEntryLink referencing the document."""
    batch = ImportBatch(
        filename="doc-test.csv",
        file_hash="d" * 64,
        status="imported",
    )
    db_session.add(batch)
    db_session.flush()

    entry = JournalEntry(
        batch_id=batch.batch_id,
        entry_number="DOC-JE-001",
        entry_date=datetime.date(2026, 1, 15),
        description="Entry linked to document",
    )
    db_session.add(entry)
    db_session.flush()

    link = DocumentEntryLink(
        document_id=document.document_id,
        entry_id=entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()

    return link


# ── list_documents Tests ─────────────────────────────────────────


class TestListDocuments:
    """Tests for SourceDocumentService.list_documents()."""

    def test_list_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        documents, total = SourceDocumentService.list_documents(db_session)

        assert documents == []
        assert total == 0

    def test_list_with_pagination(
        self, db_session: Session, five_documents: list[SourceDocument]
    ):
        """Skip/limit pagination returns correct subset."""
        documents, total = SourceDocumentService.list_documents(
            db_session, skip=0, limit=2
        )

        assert len(documents) == 2
        assert total == 5

    def test_list_ordering(
        self, db_session: Session, five_documents: list[SourceDocument]
    ):
        """Documents are ordered by document_id ASC."""
        documents, total = SourceDocumentService.list_documents(db_session)

        assert total == 5
        ids = [d.document_id for d in documents]
        assert ids == sorted(ids)


# ── get_document Tests ───────────────────────────────────────────


class TestGetDocument:
    """Tests for SourceDocumentService.get_document()."""

    def test_get_existing(
        self, db_session: Session, document: SourceDocument
    ):
        """Existing document is returned correctly."""
        result = SourceDocumentService.get_document(
            db_session, document.document_id
        )

        assert result.document_id == document.document_id
        assert result.document_number == "INV001"
        assert result.document_type == "issued_invoice"

    def test_get_nonexistent(self, db_session: Session):
        """Non-existent document_id raises ValueError."""
        with pytest.raises(
            ValueError, match="SourceDocument with ID 999 not found"
        ):
            SourceDocumentService.get_document(db_session, 999)


# ── create_document Tests ────────────────────────────────────────


class TestCreateDocument:
    """Tests for SourceDocumentService.create_document()."""

    def test_create_success(
        self, db_session: Session, doc_defaults: dict
    ):
        """Document is created with required fields and gets document_id."""
        doc = SourceDocumentService.create_document(
            db_session, doc_defaults
        )

        assert doc.document_id is not None
        assert doc.document_number == "INV001"
        assert doc.document_type == "issued_invoice"

    def test_create_missing_document_number(self, db_session: Session):
        """Missing document_number raises ValueError."""
        with pytest.raises(
            ValueError, match="document_number is required"
        ):
            SourceDocumentService.create_document(
                db_session, {"document_type": "invoice"}
            )

    def test_create_missing_document_type(self, db_session: Session):
        """Missing document_type raises ValueError."""
        with pytest.raises(
            ValueError, match="document_type is required"
        ):
            SourceDocumentService.create_document(
                db_session, {"document_number": "DOC1"}
            )


# ── update_document Tests ────────────────────────────────────────


class TestUpdateDocument:
    """Tests for SourceDocumentService.update_document()."""

    def test_update_success(
        self, db_session: Session, document: SourceDocument
    ):
        """Document number is updated successfully."""
        updated = SourceDocumentService.update_document(
            db_session,
            document.document_id,
            {"document_number": "INV001-UPDATED"},
        )

        assert updated.document_number == "INV001-UPDATED"
        assert updated.document_id == document.document_id

    def test_update_nonexistent(self, db_session: Session):
        """Non-existent document_id raises ValueError."""
        with pytest.raises(
            ValueError, match="SourceDocument with ID 999 not found"
        ):
            SourceDocumentService.update_document(db_session, 999, {})


# ── delete_document Tests ────────────────────────────────────────


class TestDeleteDocument:
    """Tests for SourceDocumentService.delete_document()."""

    def test_delete_success(
        self, db_session: Session, document: SourceDocument
    ):
        """Unused document is deleted successfully."""
        doc_id = document.document_id
        SourceDocumentService.delete_document(db_session, doc_id)

        result = (
            db_session.query(SourceDocument)
            .filter_by(document_id=doc_id)
            .first()
        )
        assert result is None

    def test_delete_nonexistent(self, db_session: Session):
        """Non-existent document_id raises ValueError."""
        with pytest.raises(
            ValueError, match="SourceDocument with ID 999 not found"
        ):
            SourceDocumentService.delete_document(db_session, 999)

    def test_delete_with_journal_entry_reference(
        self,
        db_session: Session,
        document: SourceDocument,
        document_with_entry_link: DocumentEntryLink,
    ):
        """Document referenced by journal entry via link cannot be deleted."""
        with pytest.raises(
            ValueError,
            match=(
                rf"Cannot delete SourceDocument {document.document_id}: "
                r"referenced by 1 journal entries"
            ),
        ):
            SourceDocumentService.delete_document(
                db_session, document.document_id
            )
