"""AccountType model — types of accounts in chart of accounts.

Standard account types: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE.
These define the fundamental accounting equation categories.
"""

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint

from app.models.base import Base


class AccountType(Base):
    """Account type (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE).

    Defines the fundamental accounting equation categories.
    Each account in the chart of accounts belongs to one type.
    """

    __tablename__ = "account_type"
    __table_args__ = (UniqueConstraint("code", name="uq_account_type_code"),)

    account_type_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AccountType(code={self.code!r}, name={self.name!r})>"
