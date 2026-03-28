"""SQLAlchemy Base and common mixins."""

from sqlalchemy import Column, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class UUIDMixin:
    """UUID primary key with PostgreSQL uuid_generate_v4()."""

    @declared_attr  # noqa: N805
    def id(cls):  # noqa: N805
        return Column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
            nullable=False,
        )


class TimestampMixin:
    """created_at and updated_at columns."""

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
