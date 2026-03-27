"""Database connection and session tests.

Verifies PostgreSQL connectivity via pg8000 driver, session lifecycle,
rollback behavior, and uuid-ossp extension availability.
"""

from sqlalchemy import text

from app.database import SessionLocal, engine


def test_database_connection() -> None:
    """Test PostgreSQL connection via pg8000 driver."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_session_creation() -> None:
    """Test session factory produces working sessions."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT version()"))
        version = result.scalar()
        assert version is not None
        assert "PostgreSQL" in version
    finally:
        db.close()


def test_session_rollback() -> None:
    """Test session rollback preserves session usability."""
    db = SessionLocal()
    try:
        # Start transaction
        db.execute(text("SELECT 1"))
        # Rollback
        db.rollback()
        # Session should still work after rollback
        result = db.execute(text("SELECT 2"))
        assert result.scalar() == 2
    finally:
        db.close()


def test_uuid_extension() -> None:
    """Test uuid-ossp extension generates valid UUIDs."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT uuid_generate_v4()"))
        uuid_value = result.scalar()
        assert uuid_value is not None
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 chars)
        assert len(str(uuid_value)) == 36
    finally:
        db.close()
