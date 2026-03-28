"""Tests for ImportBatch model."""

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.import_batch import ImportBatch


def test_create_import_batch(db_session):
    """Test creating import batch with all fields."""
    batch = ImportBatch(
        filename="dennik_2025.xlsx",
        file_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        imported_by="admin",
        row_count=150,
        status="imported",
        validation_report={"errors": [], "warnings": [], "rows_processed": 150},
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.batch_id is not None
    assert batch.filename == "dennik_2025.xlsx"
    assert batch.status == "imported"
    assert batch.row_count == 150
    assert batch.imported_at is not None
    assert batch.validation_report["rows_processed"] == 150


def test_status_check_constraint_valid_values(db_session):
    """Test all 4 valid status values pass CHECK constraint."""
    valid_statuses = ["pending", "validated", "imported", "rejected"]
    for i, status in enumerate(valid_statuses):
        batch = ImportBatch(
            filename=f"file_{status}.xlsx",
            file_hash=f"{status:0<64}",
            status=status,
        )
        db_session.add(batch)
    db_session.commit()

    # All 4 batches created successfully
    batches = db_session.query(ImportBatch).all()
    assert len(batches) == 4


def test_status_check_constraint_violation(db_session):
    """Test CHECK constraint on status rejects invalid value."""
    batch = ImportBatch(
        filename="invalid.xlsx",
        file_hash="1111111111111111111111111111111111111111111111111111111111111111",
        status="INVALID",
    )
    db_session.add(batch)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_unique_file_hash_constraint(db_session):
    """Test UNIQUE constraint on file_hash prevents duplicate imports."""
    same_hash = "deadbeef" * 8  # 64 chars
    batch1 = ImportBatch(
        filename="file_v1.xlsx",
        file_hash=same_hash,
        status="imported",
    )
    db_session.add(batch1)
    db_session.commit()

    batch2 = ImportBatch(
        filename="file_v2.xlsx",
        file_hash=same_hash,
        status="pending",
    )
    db_session.add(batch2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_nullable_fields(db_session):
    """Test that optional fields can be NULL."""
    batch = ImportBatch(
        filename="minimal.csv",
        file_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.batch_id is not None
    assert batch.imported_by is None
    assert batch.row_count is None
    assert batch.validation_report is None


def test_imported_at_server_default(db_session):
    """Test that imported_at gets server default (now())."""
    batch = ImportBatch(
        filename="auto_ts.xlsx",
        file_hash="cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    assert batch.imported_at is not None


def test_status_lifecycle(db_session):
    """Test status transition: pending → validated → imported."""
    batch = ImportBatch(
        filename="lifecycle.xlsx",
        file_hash="dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        status="pending",
        imported_by="system",
    )
    db_session.add(batch)
    db_session.commit()

    # Validate
    batch.status = "validated"
    batch.validation_report = {"errors": [], "warnings": ["minor format issue"]}
    db_session.commit()

    # Import
    batch.status = "imported"
    batch.row_count = 42
    db_session.commit()

    assert batch.status == "imported"
    assert batch.row_count == 42
    assert batch.validation_report["warnings"][0] == "minor format issue"


def test_rejected_with_validation_report(db_session):
    """Test rejected status with error details in validation_report."""
    batch = ImportBatch(
        filename="bad_file.xlsx",
        file_hash="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        status="rejected",
        validation_report={
            "errors": ["Missing column 'amount'", "Invalid date format in row 5"],
            "rows_processed": 0,
        },
    )
    db_session.add(batch)
    db_session.commit()

    assert batch.status == "rejected"
    assert len(batch.validation_report["errors"]) == 2
    assert "Missing column" in batch.validation_report["errors"][0]


def test_repr(db_session):
    """Test __repr__ output."""
    batch = ImportBatch(
        filename="repr_test.xlsx",
        file_hash="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()

    repr_str = repr(batch)
    assert "ImportBatch" in repr_str
    assert "repr_test.xlsx" in repr_str
    assert "pending" in repr_str
