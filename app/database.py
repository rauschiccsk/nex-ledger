"""Database connection and session management.

Provides sync SQLAlchemy engine with pg8000 driver, session factory,
and FastAPI dependency for database sessions.
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Read from environment — never hardcode credentials
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://ledger:ledger@localhost:5432/nex_ledger",
)

# Sync engine with pg8000 driver
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Sync sessionmaker
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.

    Yields a database session and ensures cleanup via try/finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
