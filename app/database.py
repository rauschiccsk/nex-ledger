"""Database connection and session management using SQLAlchemy with pg8000"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Build engine kwargs based on database type
engine_kwargs = {
    "echo": settings.ENV == "development",
    "pool_pre_ping": True,
}

# PostgreSQL-specific pool settings (not supported by SQLite StaticPool)
if settings.DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
    })

# Create engine
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
