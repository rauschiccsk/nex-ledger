"""JournalEntryLine model — riadok účtovného zápisu (double-entry)."""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import text

from app.models.base import Base


class JournalEntryLine(Base):
    """
    Riadok účtovného zápisu pre podvojné účtovníctvo.

    Tabuľka: journal_entry_line

    Stĺpce:
    - line_id: SERIAL PK
    - entry_id: INTEGER, FK→journal_entry (NOT NULL, CASCADE)
    - line_number: SMALLINT, NOT NULL
    - account_id: INTEGER, FK→account (NOT NULL, RESTRICT)
    - partner_id: INTEGER, FK→business_partner (nullable, SET NULL)
    - tax_rate_id: INTEGER, FK→tax_rate (nullable, SET NULL)
    - debit_amount: NUMERIC(15,2), server_default 0
    - credit_amount: NUMERIC(15,2), server_default 0
    - description: TEXT
    - currency_code: VARCHAR(3), FK→currency (NOT NULL, RESTRICT)

    FK (5):
    - entry_id → journal_entry.entry_id (ON DELETE CASCADE)
    - account_id → account.account_id (ON DELETE RESTRICT)
    - partner_id → business_partner.partner_id (ON DELETE SET NULL)
    - tax_rate_id → tax_rate.tax_rate_id (ON DELETE SET NULL)
    - currency_code → currency.currency_code (ON DELETE RESTRICT)

    Unique constraints:
    - (entry_id, line_number) — uq_entry_line_number
    """

    __tablename__ = "journal_entry_line"

    line_id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(
        Integer,
        ForeignKey("journal_entry.entry_id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number = Column(SmallInteger, nullable=False)
    account_id = Column(
        Integer,
        ForeignKey("account.account_id", ondelete="RESTRICT"),
        nullable=False,
    )
    partner_id = Column(
        Integer,
        ForeignKey("business_partner.partner_id", ondelete="SET NULL"),
        nullable=True,
    )
    tax_rate_id = Column(
        Integer,
        ForeignKey("tax_rate.tax_rate_id", ondelete="SET NULL"),
        nullable=True,
    )
    debit_amount = Column(Numeric(15, 2), server_default=text("0"))
    credit_amount = Column(Numeric(15, 2), server_default=text("0"))
    description = Column(Text, nullable=True)
    currency_code = Column(
        String(3),
        ForeignKey("currency.currency_code", ondelete="RESTRICT"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("entry_id", "line_number", name="uq_entry_line_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<JournalEntryLine(line_id={self.line_id}, "
            f"entry_id={self.entry_id}, line_number={self.line_number})>"
        )
