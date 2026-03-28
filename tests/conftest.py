"""
Pytest fixtures for database testing.

MANDATORY: Uses TEST_DATABASE_URL, NEVER production DATABASE_URL.
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.account import Account  # noqa: F401 — Base.metadata awareness
from app.models.account_type import AccountType  # noqa: F401 — Base.metadata awareness
from app.models.accounting_period import AccountingPeriod  # noqa: F401 — Base.metadata awareness
from app.models.base import Base
from app.models.business_partner import BusinessPartner  # noqa: F401 — Base.metadata awareness
from app.models.chart_of_accounts import ChartOfAccounts  # noqa: F401 — Base.metadata awareness
from app.models.currency import Currency  # noqa: F401 — Base.metadata awareness
from app.models.import_batch import ImportBatch  # noqa: F401 — Base.metadata awareness
from app.models.journal_entry import JournalEntry  # noqa: F401 — Base.metadata awareness
from app.models.journal_entry_line import JournalEntryLine  # noqa: F401 — Base.metadata awareness
from app.models.opening_balance import OpeningBalance  # noqa: F401 — Base.metadata awareness
from app.models.tax_rate import TaxRate  # noqa: F401 — Base.metadata awareness

# Test database URL — NEVER use production DATABASE_URL
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    settings.TEST_DATABASE_URL,
)


@pytest.fixture(scope="session")
def engine():
    """Create test database engine (session-scoped)."""
    test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)

    # Ensure uuid-ossp extension exists for UUIDMixin
    with test_engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()

    # Create all tables on test DB
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Drop all tables after entire test session
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """
    Transactional database session for each test.

    Each test gets a session bound to a transaction that is
    rolled back at the end — no data persists between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()
