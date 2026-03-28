"""Account model — accounting account with hierarchical structure.

Business rules:
- account_number: unique within chart (composite unique with chart_id)
- parent_account_id: self-FK for hierarchy (NULL = root account)
- level: hierarchy depth (1=root, 2=child, etc.)
- is_active: deactivated accounts not shown in UI but kept for history
- opening_balance / current_balance: Numeric(15,2) with server default 0
- updated_at: auto-updated via PostgreSQL trigger
"""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)

from app.models.base import Base


class Account(Base):
    """Accounting account with hierarchical structure.

    Attributes:
        account_id: Primary key
        chart_id: FK to chart_of_accounts (CASCADE delete)
        account_number: Account number within chart (UNIQUE with chart_id)
        name: Account name
        account_type_id: FK to account_type (RESTRICT delete)
        currency_code: FK to currency (RESTRICT delete)
        parent_account_id: Self-FK to parent account (SET NULL delete, NULL = root)
        level: Hierarchy level (1=root, 2=child, etc.)
        is_active: Account is active (default TRUE)
        opening_balance: Opening balance (default 0)
        current_balance: Current balance (default 0)
        updated_at: Last modification timestamp (auto-update via trigger)
    """

    __tablename__ = "account"

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    chart_id = Column(
        Integer,
        ForeignKey("chart_of_accounts.chart_id", ondelete="CASCADE"),
        nullable=False,
    )
    account_number = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    account_type_id = Column(
        Integer,
        ForeignKey("account_type.account_type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    currency_code = Column(
        String(3),
        ForeignKey("currency.currency_code", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_account_id = Column(
        Integer,
        ForeignKey("account.account_id", ondelete="SET NULL"),
        nullable=True,
    )
    level = Column(SmallInteger, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    opening_balance = Column(Numeric(15, 2), server_default=text("0"))
    current_balance = Column(Numeric(15, 2), server_default=text("0"))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("chart_id", "account_number", name="uq_chart_account_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<Account(account_id={self.account_id}, "
            f"chart_id={self.chart_id}, "
            f"account_number='{self.account_number}', "
            f"name='{self.name}')>"
        )
