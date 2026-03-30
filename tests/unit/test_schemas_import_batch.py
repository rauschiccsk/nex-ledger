"""Unit testy pre ImportBatch Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.import_batch import (
    ImportBatchCreate,
    ImportBatchRead,
    ImportBatchUpdate,
)


def test_import_batch_create_valid():
    """Test vytvorenia ImportBatchCreate s validnými dátami."""
    data = {
        "filename": "test_import.csv",
        "file_hash": "a" * 64,
        "imported_by": "admin",
    }
    schema = ImportBatchCreate(**data)
    assert schema.filename == "test_import.csv"
    assert schema.file_hash == "a" * 64
    assert schema.imported_by == "admin"


def test_import_batch_create_minimal():
    """Test vytvorenia ImportBatchCreate s minimálnymi dátami."""
    data = {
        "filename": "test.csv",
        "file_hash": "b" * 64,
    }
    schema = ImportBatchCreate(**data)
    assert schema.filename == "test.csv"
    assert schema.file_hash == "b" * 64
    assert schema.imported_by is None


def test_import_batch_create_invalid_hash_length():
    """Test validácie dĺžky hash."""
    data = {
        "filename": "test.csv",
        "file_hash": "short",
    }
    with pytest.raises(ValidationError, match="at least 64 characters"):
        ImportBatchCreate(**data)


def test_import_batch_create_invalid_hash_chars():
    """Test validácie hash formátu (len hex znaky)."""
    data = {
        "filename": "test.csv",
        "file_hash": "g" * 64,  # 'g' nie je hex znak
    }
    with pytest.raises(ValidationError, match="validný SHA256 hex string"):
        ImportBatchCreate(**data)


def test_import_batch_read_orm_mode():
    """Test čítania z ORM objektu."""

    class FakeORM:
        batch_id = 1
        filename = "import.csv"
        file_hash = "c" * 64
        row_count = 50
        imported_at = datetime.now(UTC)
        imported_by = "user@example.com"
        status = "pending"
        validation_report = None

    schema = ImportBatchRead.model_validate(FakeORM())
    assert schema.batch_id == 1
    assert schema.status == "pending"


def test_import_batch_read_invalid_status():
    """Test validácie status enum."""
    data = {
        "batch_id": 1,
        "filename": "test.csv",
        "file_hash": "d" * 64,
        "row_count": 10,
        "imported_at": datetime.now(UTC),
        "imported_by": None,
        "status": "INVALID_STATUS",
        "validation_report": None,
    }
    with pytest.raises(ValidationError, match="Status musí byť jeden z"):
        ImportBatchRead(**data)


def test_import_batch_update_partial():
    """Test partial update (všetky polia optional)."""
    data = {"row_count": 50}
    schema = ImportBatchUpdate(**data)
    assert schema.row_count == 50
    assert schema.imported_by is None


def test_import_batch_update_with_imported_by():
    """Test update s imported_by."""
    data = {
        "row_count": 100,
        "imported_by": "admin@example.com",
    }
    schema = ImportBatchUpdate(**data)
    assert schema.row_count == 100
    assert schema.imported_by == "admin@example.com"
