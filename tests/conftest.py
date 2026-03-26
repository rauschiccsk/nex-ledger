"""Pytest fixtures and configuration for NEX Ledger tests."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app

# MUST use PostgreSQL for tests — SQLite is FORBIDDEN
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+pg8000://ledger:ledger@localhost:5432/nex_ledger_test",
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine (PostgreSQL with pg8000)."""
    _engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Session:
    """Create a fresh database session for each test."""
    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = _session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client with overridden database dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
