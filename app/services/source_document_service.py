"""
SourceDocument service for NEX Ledger.

Handles CRUD operations for source documents (invoices, cash receipts).
FK guard on delete checks document_entry_link references.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document_entry_link import DocumentEntryLink
from app.models.source_document import SourceDocument


class SourceDocumentService:
    """Service for source document CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @classmethod
    def list_documents(
        cls, session: Session, skip: int = 0, limit: int = 100
    ) -> tuple[list[SourceDocument], int]:
        """
        List documents with pagination, ordered by document_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (documents list, total count)
        """
        query = session.query(SourceDocument).order_by(
            SourceDocument.document_id.asc()
        )
        total = query.count()
        documents = query.offset(skip).limit(limit).all()

        return documents, total

    @classmethod
    def get_document(
        cls, session: Session, document_id: int
    ) -> SourceDocument:
        """
        Get source document by ID.

        Args:
            session: Database session
            document_id: Source document primary key

        Returns:
            SourceDocument object

        Raises:
            ValueError: If document not found
        """
        document = (
            session.query(SourceDocument)
            .filter_by(document_id=document_id)
            .first()
        )

        if document is None:
            raise ValueError(
                f"SourceDocument with ID {document_id} not found"
            )

        return document

    @classmethod
    def create_document(
        cls, session: Session, document_data: dict
    ) -> SourceDocument:
        """
        Create a new source document.

        Args:
            session: Database session
            document_data: Dict with document fields
                (document_number and document_type required)

        Returns:
            Created SourceDocument object

        Raises:
            ValueError: If required fields are missing
        """
        if "document_number" not in document_data:
            raise ValueError("document_number is required")
        if "document_type" not in document_data:
            raise ValueError("document_type is required")

        document = SourceDocument(**document_data)
        session.add(document)
        session.flush()

        return document

    @classmethod
    def update_document(
        cls, session: Session, document_id: int, document_data: dict
    ) -> SourceDocument:
        """
        Update an existing source document.

        Args:
            session: Database session
            document_id: Document ID to update
            document_data: Dict with fields to update

        Returns:
            Updated SourceDocument object

        Raises:
            ValueError: If document not found
        """
        document = cls.get_document(session, document_id)

        for key, value in document_data.items():
            if hasattr(document, key):
                setattr(document, key, value)

        session.flush()
        return document

    @classmethod
    def delete_document(
        cls, session: Session, document_id: int
    ) -> None:
        """
        Delete a source document.

        Validates that the document is not referenced by any
        document_entry_link records (journal entry associations).

        Args:
            session: Database session
            document_id: Document ID to delete

        Raises:
            ValueError: If document not found or referenced by journal entries
        """
        document = cls.get_document(session, document_id)

        # FK guard: check document_entry_link references
        usage = session.execute(
            select(func.count(DocumentEntryLink.link_id)).where(
                DocumentEntryLink.document_id == document_id
            )
        ).scalar()

        if usage > 0:
            raise ValueError(
                f"Cannot delete SourceDocument {document_id}: "
                f"referenced by {usage} journal entries"
            )

        session.delete(document)
        session.flush()
