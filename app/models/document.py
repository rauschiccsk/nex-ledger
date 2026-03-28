"""Document model — invoices, receipts, payments, and other documents."""

import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.business_partner import BusinessPartner
    from app.models.journal_entry import JournalEntry


class DocumentType(StrEnum):
    """Document type enumeration."""

    INVOICE = "invoice"
    RECEIPT = "receipt"
    PAYMENT = "payment"
    OTHER = "other"


class Document(Base, UUIDMixin, TimestampMixin):
    """Document entity (invoices, receipts, payments)."""

    __tablename__ = "document"

    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        PG_ENUM(
            DocumentType,
            name="document_type_enum",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    document_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Foreign keys
    business_partner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partner.id", ondelete="RESTRICT"),
        nullable=False,
    )
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("journal_entry.id", ondelete="SET NULL"),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    business_partner: Mapped["BusinessPartner"] = relationship(
        "BusinessPartner",
        back_populates="documents",
    )
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship(
        "JournalEntry",
        back_populates="documents",
    )

    __table_args__ = (
        UniqueConstraint("document_number", name="uq_document_document_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<Document(number={self.document_number}, "
            f"type={self.document_type}, amount={self.amount})>"
        )
