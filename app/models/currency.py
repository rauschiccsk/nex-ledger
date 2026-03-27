"""Currency model — ISO 4217 currency definitions."""

from sqlalchemy import Boolean, CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Currency(Base, UUIDMixin, TimestampMixin):
    """Currency entity (e.g. EUR, USD, CZK)."""

    __tablename__ = "currency"

    code: Mapped[str] = mapped_column(String(3), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    decimal_places: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_currency_code"),
        CheckConstraint(
            "decimal_places >= 0 AND decimal_places <= 8",
            name="ck_currency_decimal_places",
        ),
    )

    def __repr__(self) -> str:
        return f"<Currency(code='{self.code}', name='{self.name}')>"
