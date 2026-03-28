"""
Import batch processing service for NEX Ledger.

Handles creation and status management of import batches.
"""
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
