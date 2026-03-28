"""JournalLine model — individual debit/credit line within a journal entry."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.business_partner import BusinessPartner
    from app.models.journal_entry import JournalEntry
    from app.models.tax_rate import TaxRate


class JournalLine(Base, UUIDMixin, TimestampMixin):
    """Individual debit/credit line within a journal entry."""

    __tablename__ = "journal_line"

    # FK to journal_entry (CASCADE)
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("journal_entry.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line number within entry
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # FK to account (RESTRICT)
    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("account.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Debit/Credit amounts (NUMERIC(15,2), CHECK >= 0)
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        server_default="0",
    )

    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        server_default="0",
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # FK to business_partner (SET NULL)
    business_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partner.id", ondelete="SET NULL"),
        nullable=True,
    )

    # FK to tax_rate (SET NULL)
    tax_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tax_rate.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Tax calculation fields
    tax_base_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship(
        "JournalEntry",
        back_populates="lines",
    )
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="journal_lines",
    )
    business_partner: Mapped[Optional["BusinessPartner"]] = relationship(
        "BusinessPartner",
        back_populates="journal_lines",
    )
    tax_rate: Mapped[Optional["TaxRate"]] = relationship(
        "TaxRate",
        back_populates="journal_lines",
    )

    __table_args__ = (
        UniqueConstraint(
            "journal_entry_id", "line_number", name="uq_journal_line_entry_line"
        ),
        CheckConstraint(
            "debit_amount >= 0",
            name="ck_journal_line_debit_non_negative",
        ),
        CheckConstraint(
            "credit_amount >= 0",
            name="ck_journal_line_credit_non_negative",
        ),
        CheckConstraint(
            "NOT (debit_amount > 0 AND credit_amount > 0)",
            name="ck_journal_line_debit_or_credit",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<JournalLine(entry={self.journal_entry_id}, line={self.line_number}, "
            f"debit={self.debit_amount}, credit={self.credit_amount})>"
        )
