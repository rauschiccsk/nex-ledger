"""Database connection and session management using SQLAlchemy with pg8000."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# Create engine with pg8000 driver — SQLite is FORBIDDEN
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
