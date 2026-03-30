"""
Tests for DocumentEntryLinkService CRUD operations.

Covers: list_links, get_link, create_link, delete_link.
No update_link — junction table supports only create + delete.
11 tests in 4 classes.
"""

import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.business_partner import BusinessPartner
from app.models.currency import Currency
from app.models.document_entry_link import DocumentEntryLink
from app.models.journal_entry import JournalEntry
from app.models.source_document import SourceDocument
from app.services.document_entry_link_service import DocumentEntryLinkService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def test_currency(db_session: Session) -> Currency:
    """Create EUR currency required by SourceDocument FK."""
    c = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(c)
    db_session.flush()
    return c


@pytest.fixture()
def test_partner(db_session: Session) -> BusinessPartner:
    """Create a business partner required by SourceDocument FK."""
    p = BusinessPartner(
        partner_type="CUSTOMER",
        code="LINK-CUST001",
        name="Link Test Customer",
    )
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def test_source_document(
    db_session: Session,
    test_partner: BusinessPartner,
    test_currency: Currency,
) -> SourceDocument:
    """Create a source document for linking."""
    doc = SourceDocument(
        document_number="DOC-001",
        document_type="invoice",
        issue_date=datetime.date(2026, 1, 15),
        partner_id=test_partner.partner_id,
        total_amount=Decimal("1000.00"),
        currency_code=test_currency.currency_code,
    )
    db_session.add(doc)
    db_session.flush()
    return doc


@pytest.fixture()
def test_journal_entry(db_session: Session) -> JournalEntry:
    """Create a journal entry for linking."""
    entry = JournalEntry(
        entry_number="JE-LINK-001",
        entry_date=datetime.date.today(),
    )
    db_session.add(entry)
    db_session.flush()
    return entry


@pytest.fixture()
def test_link(
    db_session: Session,
    test_source_document: SourceDocument,
    test_journal_entry: JournalEntry,
) -> DocumentEntryLink:
    """Create a document–entry link."""
    link = DocumentEntryLink(
        document_id=test_source_document.document_id,
        entry_id=test_journal_entry.entry_id,
    )
    db_session.add(link)
    db_session.flush()
    return link


@pytest.fixture()
def three_links(
    db_session: Session,
    test_partner: BusinessPartner,
    test_currency: Currency,
) -> list[DocumentEntryLink]:
    """Create 3 document–entry links for pagination testing."""
    links = []
    for i in range(1, 4):
        doc = SourceDocument(
            document_number=f"DOC-PG-{i:03d}",
            document_type="invoice",
            issue_date=datetime.date(2026, 1, i),
            partner_id=test_partner.partner_id,
            total_amount=Decimal("100.00"),
            currency_code=test_currency.currency_code,
        )
        db_session.add(doc)
        db_session.flush()

        entry = JournalEntry(
            entry_number=f"JE-PG-{i:03d}",
            entry_date=datetime.date(2026, 1, i),
        )
        db_session.add(entry)
        db_session.flush()

        link = DocumentEntryLink(
            document_id=doc.document_id,
            entry_id=entry.entry_id,
        )
        db_session.add(link)
        db_session.flush()
        links.append(link)

    return links


# ── list_links Tests ─────────────────────────────────────────────


class TestListLinks:
    """Tests for DocumentEntryLinkService.list_links()."""

    def test_list_links_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        links, total = DocumentEntryLinkService.list_links(db_session)

        assert links == []
        assert total == 0

    def test_list_links_pagination(
        self, db_session: Session, three_links: list[DocumentEntryLink]
    ):
        """Skip/limit pagination returns correct subset and total."""
        links, total = DocumentEntryLinkService.list_links(
            db_session, skip=1, limit=2
        )

        assert len(links) == 2
        assert total == 3

    def test_list_links_ordering(
        self, db_session: Session, three_links: list[DocumentEntryLink]
    ):
        """Links are ordered by link_id ASC."""
        links, total = DocumentEntryLinkService.list_links(db_session)

        assert total == 3
        ids = [link.link_id for link in links]
        assert ids == sorted(ids)


# ── get_link Tests ───────────────────────────────────────────────


class TestGetLink:
    """Tests for DocumentEntryLinkService.get_link()."""

    def test_get_link_success(
        self, db_session: Session, test_link: DocumentEntryLink
    ):
        """Existing link is returned correctly."""
        result = DocumentEntryLinkService.get_link(
            db_session, test_link.link_id
        )

        assert result.link_id == test_link.link_id
        assert result.document_id == test_link.document_id
        assert result.entry_id == test_link.entry_id

    def test_get_link_not_found(self, db_session: Session):
        """Non-existent link_id raises ValueError."""
        with pytest.raises(
            ValueError, match="DocumentEntryLink 999 not found"
        ):
            DocumentEntryLinkService.get_link(db_session, 999)


# ── create_link Tests ────────────────────────────────────────────


class TestCreateLink:
    """Tests for DocumentEntryLinkService.create_link()."""

    def test_create_link_success(
        self,
        db_session: Session,
        test_source_document: SourceDocument,
        test_journal_entry: JournalEntry,
    ):
        """Link is created with document_id + entry_id."""
        link = DocumentEntryLinkService.create_link(
            db_session,
            {
                "document_id": test_source_document.document_id,
                "entry_id": test_journal_entry.entry_id,
            },
        )

        assert link.link_id is not None
        assert link.document_id == test_source_document.document_id
        assert link.entry_id == test_journal_entry.entry_id

    def test_create_link_duplicate(
        self,
        db_session: Session,
        test_link: DocumentEntryLink,
        test_source_document: SourceDocument,
        test_journal_entry: JournalEntry,
    ):
        """Duplicate (document_id, entry_id) raises ValueError."""
        with pytest.raises(
            ValueError,
            match=(
                f"Link already exists for document "
                f"{test_source_document.document_id} "
                f"and entry {test_journal_entry.entry_id}"
            ),
        ):
            DocumentEntryLinkService.create_link(
                db_session,
                {
                    "document_id": test_source_document.document_id,
                    "entry_id": test_journal_entry.entry_id,
                },
            )

    def test_create_link_missing_fields(self, db_session: Session):
        """Missing document_id or entry_id raises ValueError."""
        with pytest.raises(
            ValueError, match="document_id and entry_id are required"
        ):
            DocumentEntryLinkService.create_link(
                db_session, {"document_id": 1}
            )

        with pytest.raises(
            ValueError, match="document_id and entry_id are required"
        ):
            DocumentEntryLinkService.create_link(
                db_session, {"entry_id": 1}
            )

    def test_create_link_invalid_document_id(
        self,
        db_session: Session,
        test_journal_entry: JournalEntry,
    ):
        """Non-existent document_id raises ValueError."""
        with pytest.raises(
            ValueError, match="SourceDocument with ID 99999 not found"
        ):
            DocumentEntryLinkService.create_link(
                db_session,
                {
                    "document_id": 99999,
                    "entry_id": test_journal_entry.entry_id,
                },
            )

    def test_create_link_invalid_entry_id(
        self,
        db_session: Session,
        test_source_document: SourceDocument,
    ):
        """Non-existent entry_id raises ValueError."""
        with pytest.raises(
            ValueError, match="JournalEntry with ID 99999 not found"
        ):
            DocumentEntryLinkService.create_link(
                db_session,
                {
                    "document_id": test_source_document.document_id,
                    "entry_id": 99999,
                },
            )


# ── delete_link Tests ────────────────────────────────────────────


class TestDeleteLink:
    """Tests for DocumentEntryLinkService.delete_link()."""

    def test_delete_link_success(
        self, db_session: Session, test_link: DocumentEntryLink
    ):
        """Existing link is deleted successfully."""
        link_id = test_link.link_id
        DocumentEntryLinkService.delete_link(db_session, link_id)

        result = (
            db_session.query(DocumentEntryLink)
            .filter_by(link_id=link_id)
            .first()
        )
        assert result is None

    def test_delete_link_not_found(self, db_session: Session):
        """Non-existent link_id raises ValueError."""
        with pytest.raises(
            ValueError, match="DocumentEntryLink 999 not found"
        ):
            DocumentEntryLinkService.delete_link(db_session, 999)
