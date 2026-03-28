"""JournalEntry model — main accounting document."""

import enum
import uuid as _uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.import_batch import ImportBatch


class EntryStatus(enum.StrEnum):
    """Status ENUM for journal entries."""

    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class JournalEntry(Base, UUIDMixin, TimestampMixin):
    """Journal entry — main accounting document."""

    __tablename__ = "journal_entry"

    entry_number: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    import_batch_id: Mapped[_uuid.UUID | None] = mapped_column(
        ForeignKey("import_batch.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[EntryStatus] = mapped_column(
        PG_ENUM(
            EntryStatus,
            name="entry_status_enum",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        server_default="draft",
    )

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    posted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    import_batch: Mapped[Optional["ImportBatch"]] = relationship(
        "ImportBatch",
        back_populates="journal_entries",
    )

    __table_args__ = (
        UniqueConstraint("entry_number", name="uq_journal_entry_entry_number"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry(entry_number='{self.entry_number}', status='{self.status}')>"
