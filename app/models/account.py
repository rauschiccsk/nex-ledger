"""Account model — chart of accounts with hierarchical structure."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Account(Base, UUIDMixin, TimestampMixin):
    """Account entity with FK to AccountType, Currency, and self-referencing hierarchy."""

    __tablename__ = "account"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Foreign keys
    account_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("account_type.id", ondelete="RESTRICT"),
        nullable=False,
    )
    currency_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("currency.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_account_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("account.id", ondelete="CASCADE"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # Relationships
    account_type: Mapped["AccountType"] = relationship(  # noqa: F821
        "AccountType", back_populates="accounts"
    )
    currency: Mapped["Currency"] = relationship(  # noqa: F821
        "Currency", back_populates="accounts"
    )
    parent_account: Mapped["Account | None"] = relationship(
        "Account",
        remote_side="Account.id",
        back_populates="sub_accounts",
    )
    sub_accounts: Mapped[list["Account"]] = relationship(
        "Account",
        back_populates="parent_account",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("code", name="uq_account_code"),)

    def __repr__(self) -> str:
        return f"<Account(code='{self.code}', name='{self.name}')>"
