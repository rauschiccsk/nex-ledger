"""Test configuration — isolated test database (NEVER touches production)."""

import os

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.base import Base


def get_test_database_url() -> str:
    """Get TEST_DATABASE_URL from env or derive from settings."""
    return os.environ.get(
        "TEST_DATABASE_URL",
        settings.test_database_url,
    )


def _create_test_db_if_not_exists() -> None:
    """Create test database if it doesn't exist (connects to 'postgres' DB)."""
    test_url = get_test_database_url()
    # Parse the DB name from URL — last segment after '/'
    db_name = test_url.rsplit("/", 1)[-1]
    # Connect to default 'postgres' DB to create test DB
    base_url = test_url.rsplit("/", 1)[0] + "/postgres"
    eng = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with eng.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db"),
            {"db": db_name},
        )
        if not result.scalar():
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    eng.dispose()


# Create test DB if needed at import time
_create_test_db_if_not_exists()

# Test engine — ALWAYS uses TEST_DATABASE_URL
test_engine = create_engine(
    get_test_database_url(),
    pool_pre_ping=True,
    echo=False,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables on test DB, enable uuid-ossp, then drop after tests."""
    with test_engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """Provide a transactional test session that rolls back after each test.

    Uses nested transaction (SAVEPOINT) pattern so that session.commit()
    inside tests does not actually persist data — the outer connection
    transaction is rolled back at teardown.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # When session.commit() is called, restart a nested SAVEPOINT
    # instead of committing the outer transaction.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
