"""Tests for ImportBatch model."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError, StatementError

from app.models.import_batch import ImportBatch, ImportBatchStatus


def test_import_batch_status_lifecycle(db_session):
    """Test batch status progression: pending → processing → completed."""
    batch = ImportBatch(
        batch_number="BATCH-20240127-001",
        source_system="Genesis",
        file_name="invoices_2024.csv",
        imported_at=datetime.now(UTC),
        imported_by="admin",
        status=ImportBatchStatus.PENDING,
        total_records=100,
        processed_records=0,
    )
    db_session.add(batch)
    db_session.commit()

    # Update to processing
    batch.status = ImportBatchStatus.PROCESSING
    batch.processed_records = 50
    db_session.commit()

    # Update to completed
    batch.status = ImportBatchStatus.COMPLETED
    batch.processed_records = 100
    db_session.commit()

    assert batch.status == ImportBatchStatus.COMPLETED
    assert batch.processed_records == batch.total_records


def test_import_batch_failed_with_error(db_session):
    """Test failed batch with error_message."""
    batch = ImportBatch(
        batch_number="BATCH-20240127-002",
        source_system="CSV Import",
        file_name="invalid.csv",
        imported_at=datetime.now(UTC),
        imported_by="admin",
        status=ImportBatchStatus.FAILED,
        total_records=50,
        processed_records=25,
        error_message="File format invalid: missing required column 'amount'",
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.status == ImportBatchStatus.FAILED
    assert batch.error_message is not None
    assert "missing required column" in batch.error_message


def test_import_batch_unique_batch_number(db_session):
    """Test UNIQUE constraint on batch_number."""
    batch1 = ImportBatch(
        batch_number="BATCH-20240127-003",
        source_system="Genesis",
        status=ImportBatchStatus.PENDING,
        imported_at=datetime.now(UTC),
        imported_by="admin",
    )
    db_session.add(batch1)
    db_session.commit()

    # Try to insert duplicate
    batch2 = ImportBatch(
        batch_number="BATCH-20240127-003",  # Same batch_number
        source_system="CSV Import",
        status=ImportBatchStatus.PENDING,
        imported_at=datetime.now(UTC),
        imported_by="admin",
    )
    db_session.add(batch2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_import_batch_invalid_status(db_session):
    """Test ENUM constraint on status (invalid value)."""
    # Try to use invalid status
    with pytest.raises((DataError, StatementError)):
        batch = ImportBatch(
            batch_number="BATCH-20240127-004",
            source_system="Genesis",
            status="invalid_status",  # Not in ENUM
            imported_at=datetime.now(UTC),
            imported_by="admin",
        )
        db_session.add(batch)
        db_session.commit()


def test_import_batch_progress_tracking(db_session):
    """Test progress tracking: processed_records <= total_records."""
    batch = ImportBatch(
        batch_number="BATCH-20240127-005",
        source_system="Genesis",
        status=ImportBatchStatus.PROCESSING,
        total_records=100,
        processed_records=0,
        imported_at=datetime.now(UTC),
        imported_by="admin",
    )
    db_session.add(batch)
    db_session.commit()

    # Simulate progress
    for i in range(1, 6):
        batch.processed_records = i * 20
        db_session.commit()
        assert batch.processed_records <= batch.total_records
