"""TaxRate model — tax rate configuration (VAT, income tax, etc.)."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TaxRate(Base, UUIDMixin, TimestampMixin):
    """Tax rate configuration (VAT, income tax, etc.)."""

    __tablename__ = "tax_rate"

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_tax_rate_code"),
        CheckConstraint(
            "rate_percent >= 0 AND rate_percent <= 100",
            name="ck_tax_rate_percent",
        ),
    )

    def __repr__(self) -> str:
        return f"<TaxRate(code={self.code!r}, rate={self.rate_percent}%, valid_from={self.valid_from})>"
