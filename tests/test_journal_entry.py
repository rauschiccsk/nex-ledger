"""Tests for JournalEntry model."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import BatchStatus, EntryStatus, ImportBatch, JournalEntry


def test_create_journal_entry_draft(db_session):
    """Test creating a draft journal entry."""
    entry = JournalEntry(
        entry_number="JE-2026-001",
        entry_date=date(2026, 3, 28),
        description="Opening balance entry",
    )
    db_session.add(entry)
    db_session.commit()

    assert entry.id is not None
    assert entry.status == EntryStatus.DRAFT
    assert entry.posted_at is None
    assert entry.posted_by is None


def test_unique_entry_number(db_session):
    """Test UNIQUE constraint on entry_number."""
    entry1 = JournalEntry(
        entry_number="JE-001",
        entry_date=date(2026, 3, 28),
    )
    db_session.add(entry1)
    db_session.commit()

    entry2 = JournalEntry(
        entry_number="JE-001",
        entry_date=date(2026, 3, 29),
    )
    db_session.add(entry2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_status_transition_draft_to_posted(db_session):
    """Test status transition from draft to posted."""
    entry = JournalEntry(
        entry_number="JE-2026-002",
        entry_date=date(2026, 3, 28),
        status=EntryStatus.DRAFT,
    )
    db_session.add(entry)
    db_session.commit()

    # Post the entry
    entry.status = EntryStatus.POSTED
    entry.posted_at = datetime.now(UTC)
    entry.posted_by = "system"
    db_session.commit()

    assert entry.status == EntryStatus.POSTED
    assert entry.posted_at is not None
    assert entry.posted_by == "system"


def test_status_transition_posted_to_cancelled(db_session):
    """Test status transition from posted to cancelled."""
    entry = JournalEntry(
        entry_number="JE-2026-003",
        entry_date=date(2026, 3, 28),
        status=EntryStatus.POSTED,
        posted_at=datetime.now(UTC),
        posted_by="user1",
    )
    db_session.add(entry)
    db_session.commit()

    # Cancel the entry
    entry.status = EntryStatus.CANCELLED
    db_session.commit()

    assert entry.status == EntryStatus.CANCELLED


def test_import_batch_relationship(db_session):
    """Test FK relationship to ImportBatch."""
    batch = ImportBatch(
        batch_number="BATCH-JE-001",
        source_system="legacy_system",
        file_name="import.csv",
        status=BatchStatus.COMPLETED,
        imported_at=datetime.now(UTC),
        imported_by="admin",
    )
    db_session.add(batch)
    db_session.commit()

    entry = JournalEntry(
        entry_number="JE-2026-004",
        entry_date=date(2026, 3, 28),
        import_batch_id=batch.id,
    )
    db_session.add(entry)
    db_session.commit()

    assert entry.import_batch.batch_number == "BATCH-JE-001"
    assert batch.journal_entries[0].entry_number == "JE-2026-004"


def test_import_batch_set_null_on_delete(db_session):
    """Test SET NULL behavior when batch is deleted."""
    batch = ImportBatch(
        batch_number="BATCH-JE-002",
        source_system="legacy_system",
        file_name="import2.csv",
        status=BatchStatus.COMPLETED,
        imported_at=datetime.now(UTC),
        imported_by="admin",
    )
    db_session.add(batch)
    db_session.commit()
    batch_id = batch.id

    entry = JournalEntry(
        entry_number="JE-2026-005",
        entry_date=date(2026, 3, 28),
        import_batch_id=batch_id,
    )
    db_session.add(entry)
    db_session.commit()
    entry_id = entry.id

    # Delete batch — FK should be SET NULL
    db_session.delete(batch)
    db_session.commit()

    # Expire to force re-fetch from DB
    db_session.expire_all()

    # Verify entry still exists but FK is NULL
    entry = db_session.get(JournalEntry, entry_id)
    assert entry is not None
    assert entry.import_batch_id is None


def test_repr(db_session):
    """Test __repr__ method."""
    entry = JournalEntry(
        entry_number="JE-2026-006",
        entry_date=date(2026, 3, 28),
        status=EntryStatus.POSTED,
    )
    db_session.add(entry)
    db_session.commit()

    repr_str = repr(entry)
    assert "JE-2026-006" in repr_str
    assert "posted" in repr_str
