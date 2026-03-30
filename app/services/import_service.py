"""
Import batch processing service for NEX Ledger.

Handles creation, CRUD operations, and state management of import batches.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.import_batch import ImportBatch


class ImportService:
    """Service for managing import batch lifecycle."""

    @staticmethod
    def create_batch(
        session: Session,
        filename: str,
        file_hash: str,
        imported_by: str | None = None,
    ) -> ImportBatch:
        """
        Create new import batch with 'pending' status.

        Args:
            session: Database session
            filename: Name of imported file (e.g., "dennik_2025.xlsx")
            file_hash: SHA-256 hash of the file (64 hex chars)
            imported_by: Username who initiated the import

        Returns:
            Created ImportBatch instance

        Example:
            >>> batch = ImportService.create_batch(
            ...     session=session,
            ...     filename="dennik_2025.xlsx",
            ...     file_hash="abc123...",
            ...     imported_by="admin"
            ... )
            >>> batch.status
            'pending'
        """
        batch = ImportBatch(
            filename=filename,
            file_hash=file_hash,
            status="pending",
            imported_by=imported_by,
        )
        session.add(batch)
        session.flush()  # Získame batch_id bez commit
        return batch

    @staticmethod
    def update_batch_status(
        session: Session,
        batch_id: int,
        status: str,
        validation_report: dict | None = None,
        row_count: int | None = None,
    ) -> ImportBatch:
        """
        Update import batch status and optional validation report.

        Args:
            session: Database session
            batch_id: Import batch ID
            status: New status (pending | validated | imported | rejected)
            validation_report: Optional JSONB validation details
            row_count: Optional number of processed rows

        Returns:
            Updated ImportBatch instance

        Raises:
            ValueError: If batch not found

        Example:
            >>> batch = ImportService.update_batch_status(
            ...     session=session,
            ...     batch_id=1,
            ...     status="validated",
            ...     row_count=150
            ... )
            >>> batch.status
            'validated'
        """
        batch = session.query(ImportBatch).filter_by(batch_id=batch_id).first()

        if not batch:
            raise ValueError(f"Import batch {batch_id} not found")

        batch.status = status
        if validation_report is not None:
            batch.validation_report = validation_report
        if row_count is not None:
            batch.row_count = row_count

        session.flush()
        return batch

    # ── CRUD Methods ─────────────────────────────────────────────

    @staticmethod
    def list_batches(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None,
    ) -> tuple[list[ImportBatch], int]:
        """
        List import batches with pagination, ordered by imported_at DESC, batch_id DESC.

        Args:
            session: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of ImportBatch, total count)
        """
        total = session.query(func.count(ImportBatch.batch_id)).scalar()

        batches = (
            session.query(ImportBatch)
            .order_by(ImportBatch.imported_at.desc(), ImportBatch.batch_id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return batches, total

    @staticmethod
    def get_batch(session: Session, batch_id: int) -> ImportBatch:
        """
        Get a single import batch by ID.

        Args:
            session: Database session
            batch_id: Import batch ID

        Returns:
            ImportBatch instance

        Raises:
            ValueError: If batch not found
        """
        batch = session.query(ImportBatch).filter_by(batch_id=batch_id).first()

        if not batch:
            raise ValueError(f"Import batch {batch_id} not found")

        return batch

    @staticmethod
    def update_batch(
        session: Session,
        batch_id: int,
        batch_data: dict,
    ) -> ImportBatch:
        """
        Update import batch attributes (not status — use state wrappers for that).

        Allowed fields: row_count, imported_by.
        Status, imported_at are NOT updatable via this method.

        Args:
            session: Database session
            batch_id: Import batch ID
            batch_data: Dict with fields to update

        Returns:
            Updated ImportBatch instance

        Raises:
            ValueError: If batch not found
        """
        batch = ImportService.get_batch(session, batch_id)

        allowed_fields = {"row_count", "imported_by"}
        for key, value in batch_data.items():
            if key in allowed_fields:
                setattr(batch, key, value)

        session.flush()
        return batch

    @staticmethod
    def delete_batch(session: Session, batch_id: int) -> None:
        """
        Delete an import batch.

        Args:
            session: Database session
            batch_id: Import batch ID

        Raises:
            ValueError: If batch not found
        """
        batch = ImportService.get_batch(session, batch_id)
        session.delete(batch)
        session.flush()

    # ── State Transition Wrappers ────────────────────────────────

    @staticmethod
    def validate_batch(session: Session, batch_id: int) -> ImportBatch:
        """
        Transition batch from 'pending' to 'validated'.

        Args:
            session: Database session
            batch_id: Import batch ID

        Returns:
            Updated ImportBatch instance

        Raises:
            ValueError: If batch not found or status is not 'pending'
        """
        batch = ImportService.get_batch(session, batch_id)

        if batch.status != "pending":
            raise ValueError(
                f"Cannot validate batch {batch_id} with status {batch.status}"
            )

        return ImportService.update_batch_status(session, batch_id, "validated")

    @staticmethod
    def import_batch(session: Session, batch_id: int) -> ImportBatch:
        """
        Transition batch from 'validated' to 'imported'.

        Args:
            session: Database session
            batch_id: Import batch ID

        Returns:
            Updated ImportBatch instance

        Raises:
            ValueError: If batch not found or status is not 'validated'
        """
        batch = ImportService.get_batch(session, batch_id)

        if batch.status != "validated":
            raise ValueError(
                f"Cannot import batch {batch_id} with status {batch.status}"
            )

        return ImportService.update_batch_status(session, batch_id, "imported")

    @staticmethod
    def reject_batch(session: Session, batch_id: int) -> ImportBatch:
        """
        Transition batch to 'rejected' (from any status except already rejected).

        Args:
            session: Database session
            batch_id: Import batch ID

        Returns:
            Updated ImportBatch instance

        Raises:
            ValueError: If batch not found or already rejected
        """
        batch = ImportService.get_batch(session, batch_id)

        if batch.status == "rejected":
            raise ValueError(
                f"Batch {batch_id} is already rejected"
            )

        return ImportService.update_batch_status(session, batch_id, "rejected")
