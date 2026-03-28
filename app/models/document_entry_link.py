"""DocumentEntryLink model — many-to-many link between source_document and journal_entry.

Business rules:
- document_id: FK → source_document (CASCADE — link removed when document deleted)
- entry_id: FK → journal_entry (CASCADE — link removed when entry deleted)
- (document_id, entry_id) must be unique — one link per document-entry pair
- created_at: automatic timestamp of link creation
"""

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)

from app.models.base import Base


class DocumentEntryLink(Base):
    """Link between source document and journal entry (many-to-many).

    Attributes:
        link_id: Primary key (SERIAL)
        document_id: FK to source_document (CASCADE delete)
        entry_id: FK to journal_entry (CASCADE delete)
        created_at: Timestamp of link creation (auto-set by DB)
    """

    __tablename__ = "document_entry_link"

    link_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("source_document.document_id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_id = Column(
        Integer,
        ForeignKey("journal_entry.entry_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("document_id", "entry_id", name="uq_document_entry"),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentEntryLink(link_id={self.link_id}, "
            f"document_id={self.document_id}, "
            f"entry_id={self.entry_id})>"
        )
