"""Tests for JournalEntry model."""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.import_batch import ImportBatch
from app.models.journal_entry import JournalEntry


def test_create_entry_with_batch(db_session):
    """Test vytvorenie journal entry s batch_id."""
    batch = ImportBatch(
        filename="test.csv",
        file_hash="a" * 64,
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()

    entry = JournalEntry(
        batch_id=batch.batch_id,
        entry_number="JE-2026-001",
        entry_date=date(2026, 3, 28),
        description="Test journal entry",
        created_by="test_user",
    )
    db_session.add(entry)
    db_session.commit()

    assert entry.entry_id is not None
    assert entry.batch_id == batch.batch_id
    assert entry.entry_number == "JE-2026-001"
    assert entry.entry_date == date(2026, 3, 28)
    assert entry.description == "Test journal entry"
    assert entry.created_by == "test_user"
    assert entry.created_at is not None


def test_create_entry_without_batch(db_session):
    """Test vytvorenie journal entry bez batch_id (NULL FK)."""
    entry = JournalEntry(
        batch_id=None,
        entry_number="JE-2026-002",
        entry_date=date(2026, 3, 28),
        description="Standalone entry",
    )
    db_session.add(entry)
    db_session.commit()

    assert entry.entry_id is not None
    assert entry.batch_id is None
    assert entry.entry_number == "JE-2026-002"


def test_unique_entry_number(db_session):
    """Test UNIQUE constraint na entry_number."""
    entry1 = JournalEntry(
        entry_number="JE-2026-003",
        entry_date=date(2026, 3, 28),
    )
    db_session.add(entry1)
    db_session.commit()

    entry2 = JournalEntry(
        entry_number="JE-2026-003",
        entry_date=date(2026, 3, 29),
    )
    db_session.add(entry2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_batch_delete_sets_null(db_session):
    """Test ON DELETE SET NULL behavior pri delete batch."""
    batch = ImportBatch(
        filename="test_del.csv",
        file_hash="b" * 64,
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()
    batch_id = batch.batch_id

    entry = JournalEntry(
        batch_id=batch_id,
        entry_number="JE-2026-004",
        entry_date=date(2026, 3, 28),
    )
    db_session.add(entry)
    db_session.commit()
    entry_id = entry.entry_id

    # Delete batch via raw SQL to avoid ORM relationship issues
    db_session.execute(
        text("DELETE FROM import_batch WHERE batch_id = :id"),
        {"id": batch_id},
    )
    db_session.commit()

    # Expire cached state and re-fetch
    db_session.expire_all()
    entry = db_session.query(JournalEntry).filter_by(entry_id=entry_id).one()
    assert entry.batch_id is None


def test_required_fields(db_session):
    """Test povinné polia — entry_number NOT NULL.

    pg8000 maps NOT NULL violation (23502) to ProgrammingError, not IntegrityError.
    """
    entry = JournalEntry(
        entry_number=None,
        entry_date=date(2026, 3, 28),
    )
    db_session.add(entry)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_repr(db_session):
    """Test __repr__ metódy."""
    entry = JournalEntry(
        entry_number="JE-2026-005",
        entry_date=date(2026, 3, 28),
    )
    db_session.add(entry)
    db_session.commit()

    assert "JournalEntry" in repr(entry)
    assert "JE-2026-005" in repr(entry)
