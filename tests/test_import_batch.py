"""Tests for ImportBatch model."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.import_batch import BatchStatus, ImportBatch


def test_create_import_batch(db_session):
    """Test creating an import batch with all fields."""
    batch = ImportBatch(
        batch_number="BATCH-2026-001",
        source_system="ERP-LEGACY",
        file_name="invoices_2026_q1.csv",
        imported_at=datetime(2026, 3, 28, 10, 0, 0),
        imported_by="admin",
        status=BatchStatus.PENDING,
        total_records=100,
        processed_records=0,
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.id is not None
    assert batch.batch_number == "BATCH-2026-001"
    assert batch.status == BatchStatus.PENDING
    assert batch.total_records == 100
    assert batch.processed_records == 0


def test_batch_number_unique_constraint(db_session):
    """Test UNIQUE constraint on batch_number."""
    batch1 = ImportBatch(
        batch_number="BATCH-2026-002",
        source_system="ERP",
        file_name="data.csv",
        imported_at=datetime.now(),
        imported_by="user1",
    )
    db_session.add(batch1)
    db_session.commit()

    batch2 = ImportBatch(
        batch_number="BATCH-2026-002",  # Duplicate
        source_system="CRM",
        file_name="other.csv",
        imported_at=datetime.now(),
        imported_by="user2",
    )
    db_session.add(batch2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_status_transitions(db_session):
    """Test batch status lifecycle."""
    batch = ImportBatch(
        batch_number="BATCH-2026-003",
        source_system="WM",
        file_name="products.xlsx",
        imported_at=datetime.now(),
        imported_by="admin",
        status=BatchStatus.PENDING,
    )
    db_session.add(batch)
    db_session.commit()

    # Start processing
    batch.status = BatchStatus.PROCESSING
    batch.processed_records = 50
    db_session.commit()
    assert batch.status == BatchStatus.PROCESSING

    # Complete
    batch.status = BatchStatus.COMPLETED
    batch.processed_records = batch.total_records
    db_session.commit()
    assert batch.status == BatchStatus.COMPLETED


def test_failed_batch_with_error_message(db_session):
    """Test batch failure with error logging."""
    batch = ImportBatch(
        batch_number="BATCH-2026-004",
        source_system="API",
        file_name="transactions.json",
        imported_at=datetime.now(),
        imported_by="system",
        status=BatchStatus.FAILED,
        total_records=200,
        processed_records=150,
        error_message="Database connection lost at record 150",
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.status == BatchStatus.FAILED
    assert batch.error_message is not None
    assert "connection lost" in batch.error_message


def test_server_defaults(db_session):
    """Test server_default values for status and counters."""
    batch = ImportBatch(
        batch_number="BATCH-2026-005",
        source_system="SFTP",
        file_name="data.csv",
        imported_at=datetime.now(),
        imported_by="cron",
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)  # Fetch server defaults

    assert batch.status == BatchStatus.PENDING  # server_default
    assert batch.total_records == 0  # server_default
    assert batch.processed_records == 0  # server_default


def test_partial_processing(db_session):
    """Test batch with partial processing."""
    batch = ImportBatch(
        batch_number="BATCH-2026-006",
        source_system="EDI",
        file_name="orders.xml",
        imported_at=datetime.now(),
        imported_by="integration",
        total_records=1000,
        processed_records=750,
        status=BatchStatus.PROCESSING,
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.processed_records < batch.total_records


def test_repr(db_session):
    """Test __repr__ output."""
    batch = ImportBatch(
        batch_number="BATCH-2026-007",
        source_system="TEST",
        file_name="test.csv",
        imported_at=datetime.now(),
        imported_by="tester",
        status=BatchStatus.COMPLETED,
    )
    db_session.add(batch)
    db_session.commit()

    repr_str = repr(batch)
    assert "ImportBatch" in repr_str
    assert "BATCH-2026-007" in repr_str
    assert "completed" in repr_str
