"""OpeningBalance model — počiatočné stavy účtov pre účtovné obdobie.

Business rules:
- period_id: FK na accounting_period (CASCADE — zmazanie obdobia zmaže aj stavy)
- account_id: FK na account (CASCADE — zmazanie účtu zmaže aj stav)
- debit_amount / credit_amount: NUMERIC(15,2) so server_default 0
- Unique constraint: (period_id, account_id) — jeden počiatočný stav per účet per obdobie
"""

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
    text,
)

from app.models.base import Base


class OpeningBalance(Base):
    """Opening balance per account per accounting period.

    Attributes:
        balance_id: Primary key (SERIAL)
        period_id: FK to accounting_period (CASCADE delete)
        account_id: FK to account (CASCADE delete)
        debit_amount: Debit opening balance (default 0)
        credit_amount: Credit opening balance (default 0)
        created_at: Timestamp of record creation (auto-set by DB)
    """

    __tablename__ = "opening_balance"

    balance_id = Column(Integer, primary_key=True, autoincrement=True)
    period_id = Column(
        Integer,
        ForeignKey("accounting_period.period_id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id = Column(
        Integer,
        ForeignKey("account.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    debit_amount = Column(Numeric(15, 2), server_default=text("0"))
    credit_amount = Column(Numeric(15, 2), server_default=text("0"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("period_id", "account_id", name="uq_period_account"),
    )

    def __repr__(self) -> str:
        return (
            f"<OpeningBalance(balance_id={self.balance_id}, "
            f"period_id={self.period_id}, account_id={self.account_id}, "
            f"debit={self.debit_amount}, credit={self.credit_amount})>"
        )
