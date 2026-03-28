"""Database connection and session management (synchronous pg8000)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# Sync engine with pg8000 dialect
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,
)

# Sync sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:  # type: ignore[misc]
    """FastAPI dependency — sync session in threadpool."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
