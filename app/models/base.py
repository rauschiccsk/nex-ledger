"""SQLAlchemy Base and common mixins.

Provides declarative Base, UUIDMixin with PostgreSQL uuid_generate_v4(),
and TimestampMixin with server-side timestamps.
"""

from sqlalchemy import Column, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UUIDMixin:
    """UUID primary key using PostgreSQL uuid_generate_v4().

    Server-side UUID generation — no Python uuid.uuid4() in model definitions.
    Requires CREATE EXTENSION IF NOT EXISTS "uuid-ossp" migration.
    """

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )


class TimestampMixin:
    """Created and updated timestamps with server-side defaults."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
