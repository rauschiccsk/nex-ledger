"""Account Type model — účtové typy pre dvojité účtovníctvo."""

from enum import StrEnum

from sqlalchemy import Boolean, Column, Enum, String, UniqueConstraint

from app.models.base import Base, TimestampMixin, UUIDMixin


class AccountCategory(StrEnum):
    """Kategória účtu — asset, liability, equity, revenue, expense."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalance(StrEnum):
    """Normálny zostatok účtu — debit (ľavá strana) alebo credit (pravá strana)."""

    DEBIT = "debit"
    CREDIT = "credit"


class AccountType(Base, UUIDMixin, TimestampMixin):
    """Account Type — typ účtu v účtovej osnove.

    Príklady:
    - code="1XX", name="Aktíva", category=ASSET, normal_balance=DEBIT
    - code="2XX", name="Pasíva", category=LIABILITY, normal_balance=CREDIT
    """

    __tablename__ = "account_type"

    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(
        Enum(
            AccountCategory,
            name="account_category_enum",
            create_type=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    normal_balance = Column(
        Enum(
            NormalBalance,
            name="normal_balance_enum",
            create_type=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    is_system = Column(Boolean, default=False, nullable=False, server_default="false")

    __table_args__ = (UniqueConstraint("code", name="uq_account_type_code"),)

    def __repr__(self) -> str:
        return f"<AccountType(code={self.code}, name={self.name}, category={self.category.value})>"
