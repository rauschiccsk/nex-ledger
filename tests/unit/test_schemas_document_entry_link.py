"""Unit testy pre DocumentEntryLink Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.document_entry_link import (
    DocumentEntryLinkCreate,
    DocumentEntryLinkRead,
)


def test_document_entry_link_create_valid():
    """Test vytvorenia validného DocumentEntryLinkCreate."""
    data = {
        "document_id": 1,
        "entry_id": 2,
    }
    link = DocumentEntryLinkCreate(**data)
    assert link.document_id == 1
    assert link.entry_id == 2


def test_document_entry_link_create_fk_validation():
    """Test validácie FK constraints (document_id, entry_id > 0)."""
    # document_id musí byť > 0
    with pytest.raises(ValidationError) as exc_info:
        DocumentEntryLinkCreate(document_id=0, entry_id=1)
    assert "greater than 0" in str(exc_info.value)

    # entry_id musí byť > 0
    with pytest.raises(ValidationError) as exc_info:
        DocumentEntryLinkCreate(document_id=1, entry_id=0)
    assert "greater than 0" in str(exc_info.value)


def test_document_entry_link_read_from_orm():
    """Test ORM mode pre DocumentEntryLinkRead."""

    class FakeORM:
        link_id = 1
        document_id = 10
        entry_id = 20
        created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

    link = DocumentEntryLinkRead.model_validate(FakeORM())
    assert link.link_id == 1
    assert link.document_id == 10
    assert link.entry_id == 20
    assert link.created_at == datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_document_entry_link_read_all_fields():
    """Test všetkých povinných fieldov v DocumentEntryLinkRead."""
    data = {
        "link_id": 1,
        "document_id": 10,
        "entry_id": 20,
        "created_at": datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
    }
    link = DocumentEntryLinkRead(**data)
    assert link.link_id == 1
    assert link.document_id == 10
    assert link.entry_id == 20


def test_no_update_schema_exists():
    """Overenie že DocumentEntryLinkUpdate schema NEEXISTUJE."""
    with pytest.raises(ImportError):
        from app.schemas.document_entry_link import DocumentEntryLinkUpdate  # noqa: F401


def test_document_entry_link_create_missing_fields():
    """Test že Create vyžaduje oba FK fieldy."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentEntryLinkCreate(document_id=1)  # chýba entry_id
    assert "entry_id" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        DocumentEntryLinkCreate(entry_id=1)  # chýba document_id
    assert "document_id" in str(exc_info.value)
