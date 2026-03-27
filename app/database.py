"""Database connection and session management.

Provides sync SQLAlchemy engine with pg8000 driver, session factory,
and FastAPI dependency for database sessions.
"""

from collections.abc import Generator

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    database_url: str = "postgresql+pg8000://ledger:ledger@localhost:5432/nex_ledger"
    secret_key: str = "change-this-secret-key-in-production"
    port: int = 9180
    debug: bool = False
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()

# Sync engine with pg8000 driver
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
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
