"""AccountType model — chart of accounts type definitions."""

import enum

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AccountCategory(enum.StrEnum):
    """Accounting category (asset, liability, equity, revenue, expense)."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalance(enum.StrEnum):
    """Normal balance side (debit or credit)."""

    DEBIT = "debit"
    CREDIT = "credit"


class AccountType(Base, UUIDMixin, TimestampMixin):
    """Account type entity for chart of accounts."""

    __tablename__ = "account_type"

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[AccountCategory] = mapped_column(
        PG_ENUM(
            AccountCategory,
            name="account_category",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    normal_balance: Mapped[NormalBalance] = mapped_column(
        PG_ENUM(
            NormalBalance,
            name="normal_balance",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_account_type_code"),
    )

    def __repr__(self) -> str:
        return f"<AccountType {self.code}: {self.name} ({self.category.value})>"
