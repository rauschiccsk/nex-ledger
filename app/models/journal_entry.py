"""JournalEntry model — účtovný zápis (hlavička)."""

from sqlalchemy import (
    TIMESTAMP,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from app.models.base import Base


class JournalEntry(Base):
    """
    Hlavička účtovného zápisu.

    Tabuľka: journal_entry

    Stĺpce:
    - entry_id: SERIAL PK
    - batch_id: INTEGER, FK→import_batch (nullable, SET NULL)
    - entry_number: VARCHAR(50), UNIQUE, NOT NULL
    - entry_date: DATE, NOT NULL
    - description: TEXT
    - created_at: TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT NOW()
    - created_by: VARCHAR(100)

    FK:
    - batch_id → import_batch.batch_id (ON DELETE SET NULL)

    Unique constraints:
    - entry_number (uq_journal_entry_entry_number)
    """

    __tablename__ = "journal_entry"

    entry_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(
        Integer,
        ForeignKey("import_batch.batch_id", ondelete="SET NULL"),
        nullable=True,
    )
    entry_number = Column(String(50), nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("entry_number", name="uq_journal_entry_entry_number"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry(entry_id={self.entry_id}, entry_number='{self.entry_number}')>"
