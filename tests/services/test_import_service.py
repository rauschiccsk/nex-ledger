"""
Tests for ImportService — batch status management.
"""
import pytest
from sqlalchemy.orm import Session

from app.models.import_batch import ImportBatch
from app.services.import_service import ImportService


def test_create_batch(db_session: Session):
    """Test batch creation with 'pending' status."""
    batch = ImportService.create_batch(
        session=db_session,
        filename="dennik_2025.xlsx",
        file_hash="a" * 64,
        imported_by="test_user",
    )

    assert batch.batch_id is not None
    assert batch.filename == "dennik_2025.xlsx"
    assert batch.file_hash == "a" * 64
    assert batch.status == "pending"
    assert batch.imported_by == "test_user"
    assert batch.imported_at is not None
    assert batch.validation_report is None
    assert batch.row_count is None


def test_update_batch_status_pending_to_validated(db_session: Session):
    """Test status transition: pending → validated."""
    batch = ImportService.create_batch(
        session=db_session,
        filename="test.csv",
        file_hash="b" * 64,
        imported_by="admin",
    )
    db_session.commit()

    updated = ImportService.update_batch_status(
        session=db_session,
        batch_id=batch.batch_id,
        status="validated",
        row_count=150,
    )
    db_session.commit()

    assert updated.status == "validated"
    assert updated.row_count == 150
    assert updated.validation_report is None


def test_update_batch_status_validated_to_imported(db_session: Session):
    """Test status transition: validated → imported."""
    batch = ImportService.create_batch(
        session=db_session,
        filename="test2.csv",
        file_hash="c" * 64,
        imported_by="admin",
    )
    ImportService.update_batch_status(
        session=db_session,
        batch_id=batch.batch_id,
        status="validated",
    )
    db_session.commit()

    updated = ImportService.update_batch_status(
        session=db_session,
        batch_id=batch.batch_id,
        status="imported",
    )
    db_session.commit()

    assert updated.status == "imported"


def test_update_batch_status_pending_to_rejected(db_session: Session):
    """Test status transition: pending → rejected with validation report."""
    batch = ImportService.create_batch(
        session=db_session,
        filename="invalid.csv",
        file_hash="d" * 64,
        imported_by="admin",
    )
    db_session.commit()

    report = {"errors": ["Missing required column 'amount'"], "warnings": []}
    updated = ImportService.update_batch_status(
        session=db_session,
        batch_id=batch.batch_id,
        status="rejected",
        validation_report=report,
    )
    db_session.commit()

    assert updated.status == "rejected"
    assert updated.validation_report == report


def test_update_with_validation_report(db_session: Session):
    """Test validation_report persistence across updates."""
    batch = ImportService.create_batch(
        session=db_session,
        filename="report_test.csv",
        file_hash="e" * 64,
        imported_by="admin",
    )
    db_session.commit()

    # First update — set validation report with warning
    report1 = {"warnings": ["Duplicate entry on row 5"], "errors": []}
    ImportService.update_batch_status(
        session=db_session,
        batch_id=batch.batch_id,
        status="validated",
        validation_report=report1,
    )
    db_session.commit()

    refreshed = (
        db_session.query(ImportBatch)
        .filter_by(batch_id=batch.batch_id)
        .first()
    )
    assert refreshed.validation_report == report1

    # Second update — replace validation report with error
    report2 = {
        "warnings": ["Duplicate entry on row 5"],
        "errors": ["Validation failed on line 42"],
    }
    ImportService.update_batch_status(
        session=db_session,
        batch_id=batch.batch_id,
        status="rejected",
        validation_report=report2,
    )
    db_session.commit()

    final = (
        db_session.query(ImportBatch)
        .filter_by(batch_id=batch.batch_id)
        .first()
    )
    assert final.status == "rejected"
    assert final.validation_report == report2


def test_update_batch_status_not_found(db_session: Session):
    """Test update with non-existent batch_id raises ValueError."""
    with pytest.raises(ValueError, match="Import batch 999 not found"):
        ImportService.update_batch_status(
            session=db_session,
            batch_id=999,
            status="imported",
        )
