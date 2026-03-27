"""Database connection and UUID generation tests."""

from uuid import UUID

import pytest
from sqlalchemy import text

from tests.conftest import TestSessionLocal, test_engine


def test_database_connection():
    """Test PostgreSQL connection via pg8000 (uses test DB)."""
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS value"))
        assert result.scalar() == 1


def test_session_rollback():
    """Test session rollback on exception."""
    db = TestSessionLocal()
    try:
        # Create a temp table
        db.execute(text("CREATE TEMP TABLE test_rollback (id INT)"))
        db.execute(text("INSERT INTO test_rollback VALUES (1)"))

        # Force rollback by raising exception
        raise ValueError("Test rollback")
    except ValueError:
        db.rollback()
    finally:
        db.close()

    # Verify temp table doesn't exist after rollback (temp tables are session-scoped)
    db = TestSessionLocal()
    try:
        with pytest.raises(Exception):
            db.execute(text("SELECT * FROM test_rollback"))
            db.commit()
    finally:
        db.close()


def test_uuid_extension():
    """Test uuid-ossp extension and uuid_generate_v4()."""
    with test_engine.connect() as conn:
        # Check extension exists
        result = conn.execute(
            text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'uuid-ossp'")
        )
        assert result.scalar() == 1

        # Test uuid_generate_v4()
        result = conn.execute(text("SELECT uuid_generate_v4() AS id"))
        uuid_val = result.scalar()
        assert isinstance(uuid_val, UUID)
        assert uuid_val.version == 4
