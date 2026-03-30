"""
Tests for ImportService CRUD operations and state transition wrappers.
"""
import pytest
from sqlalchemy.orm import Session

from app.models.import_batch import ImportBatch
from app.services.import_service import ImportService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def sample_batch(db_session: Session) -> ImportBatch:
    """Create a single pending import batch."""
    return ImportService.create_batch(
        session=db_session,
        filename="dennik_2025.xlsx",
        file_hash="a" * 64,
        imported_by="test_user",
    )


@pytest.fixture()
def multiple_batches(db_session: Session) -> list[ImportBatch]:
    """Create 5 batches for pagination testing."""
    batches = []
    for i in range(5):
        batch = ImportService.create_batch(
            session=db_session,
            filename=f"file_{i}.csv",
            file_hash=f"{i}" * 64,
            imported_by="test_user",
        )
        batches.append(batch)
    return batches


# ── CRUD Tests ───────────────────────────────────────────────────


class TestListBatches:
    """Tests for ImportService.list_batches()."""

    def test_list_batches_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        batches, total = ImportService.list_batches(db_session)

        assert batches == []
        assert total == 0

    def test_list_batches_pagination(
        self, db_session: Session, multiple_batches: list[ImportBatch]
    ):
        """Skip/limit pagination returns correct subset."""
        # Get second page (2 items per page)
        batches, total = ImportService.list_batches(db_session, skip=2, limit=2)

        assert len(batches) == 2
        assert total == 5

    def test_list_batches_ordering(
        self, db_session: Session, multiple_batches: list[ImportBatch]
    ):
        """Batches are ordered by imported_at DESC, batch_id DESC."""
        batches, total = ImportService.list_batches(db_session)

        assert total == 5
        assert len(batches) == 5

        # batch_ids should be in descending order (same imported_at → fallback to id DESC)
        batch_ids = [b.batch_id for b in batches]
        assert batch_ids == sorted(batch_ids, reverse=True)


class TestGetBatch:
    """Tests for ImportService.get_batch()."""

    def test_get_batch_success(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Existing batch is returned correctly."""
        result = ImportService.get_batch(db_session, sample_batch.batch_id)

        assert result.batch_id == sample_batch.batch_id
        assert result.filename == "dennik_2025.xlsx"
        assert result.status == "pending"

    def test_get_batch_not_found(self, db_session: Session):
        """Non-existent batch raises ValueError."""
        with pytest.raises(ValueError, match="Import batch 99999 not found"):
            ImportService.get_batch(db_session, 99999)


class TestUpdateBatch:
    """Tests for ImportService.update_batch()."""

    def test_update_batch_success(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Update allowed fields (row_count, imported_by)."""
        updated = ImportService.update_batch(
            db_session,
            sample_batch.batch_id,
            {"row_count": 42, "imported_by": "new_user"},
        )

        assert updated.row_count == 42
        assert updated.imported_by == "new_user"
        # Status should remain unchanged
        assert updated.status == "pending"

    def test_update_batch_ignores_disallowed_fields(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Fields outside allowed_fields (filename) are silently ignored."""
        original_filename = sample_batch.filename
        updated = ImportService.update_batch(
            db_session,
            sample_batch.batch_id,
            {"filename": "should_not_change.csv", "row_count": 10},
        )

        assert updated.filename == original_filename
        assert updated.row_count == 10

    def test_update_batch_not_found(self, db_session: Session):
        """Non-existent batch raises ValueError."""
        with pytest.raises(ValueError, match="Import batch 99999 not found"):
            ImportService.update_batch(db_session, 99999, {"row_count": 1})


class TestDeleteBatch:
    """Tests for ImportService.delete_batch()."""

    def test_delete_batch_success(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Batch is deleted from database."""
        batch_id = sample_batch.batch_id
        ImportService.delete_batch(db_session, batch_id)

        # Verify batch no longer exists
        result = (
            db_session.query(ImportBatch)
            .filter_by(batch_id=batch_id)
            .first()
        )
        assert result is None

    def test_delete_batch_not_found(self, db_session: Session):
        """Non-existent batch raises ValueError."""
        with pytest.raises(ValueError, match="Import batch 99999 not found"):
            ImportService.delete_batch(db_session, 99999)


# ── State Transition Tests ───────────────────────────────────────


class TestValidateBatch:
    """Tests for ImportService.validate_batch()."""

    def test_validate_batch_from_pending(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Pending batch transitions to validated."""
        result = ImportService.validate_batch(db_session, sample_batch.batch_id)

        assert result.status == "validated"
        assert result.batch_id == sample_batch.batch_id

    def test_validate_batch_invalid_status(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """ValueError if batch is not in 'pending' status."""
        # Move to validated first
        ImportService.update_batch_status(
            db_session, sample_batch.batch_id, "validated"
        )

        with pytest.raises(ValueError, match="Cannot validate batch"):
            ImportService.validate_batch(db_session, sample_batch.batch_id)


class TestImportBatchTransition:
    """Tests for ImportService.import_batch()."""

    def test_import_batch_from_validated(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Validated batch transitions to imported."""
        # First validate
        ImportService.update_batch_status(
            db_session, sample_batch.batch_id, "validated"
        )

        result = ImportService.import_batch(db_session, sample_batch.batch_id)

        assert result.status == "imported"

    def test_import_batch_invalid_status(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """ValueError if batch is not in 'validated' status."""
        # Batch is still 'pending'
        with pytest.raises(ValueError, match="Cannot import batch"):
            ImportService.import_batch(db_session, sample_batch.batch_id)


class TestRejectBatch:
    """Tests for ImportService.reject_batch()."""

    def test_reject_batch_from_pending(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Pending batch can be rejected."""
        result = ImportService.reject_batch(db_session, sample_batch.batch_id)

        assert result.status == "rejected"

    def test_reject_batch_from_validated(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Validated batch can be rejected."""
        ImportService.update_batch_status(
            db_session, sample_batch.batch_id, "validated"
        )

        result = ImportService.reject_batch(db_session, sample_batch.batch_id)

        assert result.status == "rejected"

    def test_reject_batch_from_imported(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """Batch can be rejected from 'imported' status (any → rejected)."""
        ImportService.update_batch_status(
            db_session, sample_batch.batch_id, "validated"
        )
        ImportService.update_batch_status(
            db_session, sample_batch.batch_id, "imported"
        )

        result = ImportService.reject_batch(db_session, sample_batch.batch_id)
        assert result.status == "rejected"

    def test_reject_batch_already_rejected(
        self, db_session: Session, sample_batch: ImportBatch
    ):
        """ValueError if batch is already rejected."""
        ImportService.reject_batch(db_session, sample_batch.batch_id)

        with pytest.raises(ValueError, match="already rejected"):
            ImportService.reject_batch(db_session, sample_batch.batch_id)
