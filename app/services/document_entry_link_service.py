"""
DocumentEntryLink service for NEX Ledger.

Handles CRUD operations for document-entry links (junction table).
No update_link() — junction table supports only create + delete.
"""

from sqlalchemy.orm import Session

from app.models.document_entry_link import DocumentEntryLink
from app.models.journal_entry import JournalEntry
from app.models.source_document import SourceDocument


class DocumentEntryLinkService:
    """Service for document–entry link CRUD operations (no update)."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_links(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[DocumentEntryLink], int]:
        """
        List links with pagination, ordered by link_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters (reserved for future use)

        Returns:
            Tuple of (links list, total count)
        """
        total = session.query(DocumentEntryLink).count()
        links = (
            session.query(DocumentEntryLink)
            .order_by(DocumentEntryLink.link_id.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return links, total

    @staticmethod
    def get_link(
        session: Session, link_id: int
    ) -> DocumentEntryLink:
        """
        Get link by ID.

        Args:
            session: Database session
            link_id: Link primary key

        Returns:
            DocumentEntryLink object

        Raises:
            ValueError: If link not found
        """
        link = (
            session.query(DocumentEntryLink)
            .filter(DocumentEntryLink.link_id == link_id)
            .first()
        )

        if link is None:
            raise ValueError(f"DocumentEntryLink {link_id} not found")

        return link

    @staticmethod
    def create_link(
        session: Session, link_data: dict
    ) -> DocumentEntryLink:
        """
        Create a new document–entry link.

        Validates:
        - document_id and entry_id are present
        - No duplicate link for (document_id, entry_id)
        - Referenced SourceDocument and JournalEntry exist

        Args:
            session: Database session
            link_data: Dict with document_id and entry_id

        Returns:
            Created DocumentEntryLink object

        Raises:
            ValueError: If validation fails
        """
        document_id = link_data.get("document_id")
        entry_id = link_data.get("entry_id")

        if not document_id or not entry_id:
            raise ValueError("document_id and entry_id are required")

        # UNIQUE check
        existing = (
            session.query(DocumentEntryLink)
            .filter_by(document_id=document_id, entry_id=entry_id)
            .first()
        )
        if existing:
            raise ValueError(
                f"Link already exists for document {document_id} "
                f"and entry {entry_id}"
            )

        # FK validation — SourceDocument
        source_doc = session.get(SourceDocument, document_id)
        if source_doc is None:
            raise ValueError(
                f"SourceDocument with ID {document_id} not found"
            )

        # FK validation — JournalEntry
        journal_entry = session.get(JournalEntry, entry_id)
        if journal_entry is None:
            raise ValueError(
                f"JournalEntry with ID {entry_id} not found"
            )

        link = DocumentEntryLink(**link_data)
        session.add(link)
        session.flush()

        return link

    @staticmethod
    def delete_link(
        session: Session, link_id: int
    ) -> None:
        """
        Delete a document–entry link.

        Args:
            session: Database session
            link_id: Link ID to delete

        Raises:
            ValueError: If link not found
        """
        link = DocumentEntryLinkService.get_link(session, link_id)
        session.delete(link)
        session.flush()
