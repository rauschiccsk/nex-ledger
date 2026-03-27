"""Currency model for NEX Ledger."""

from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String

from app.models.base import Base, TimestampMixin, UUIDMixin


class Currency(Base, UUIDMixin, TimestampMixin):
    """Currency entity with ISO 4217 code support."""

    __tablename__ = "currency"

    code = Column(
        String(3),
        unique=True,
        nullable=False,
        index=True,
        comment="ISO 4217 currency code (e.g., EUR, USD, CZK)",
    )
    name = Column(
        String(100),
        nullable=False,
        comment="Full currency name (e.g., Euro, US Dollar)",
    )
    symbol = Column(
        String(10),
        nullable=False,
        comment="Currency symbol (e.g., \u20ac, $, K\u010d)",
    )
    decimal_places = Column(
        Integer,
        nullable=False,
        comment="Number of decimal places (0-8)",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Currency is active for use",
    )

    __table_args__ = (
        CheckConstraint(
            "decimal_places >= 0 AND decimal_places <= 8",
            name="ck_currency_decimal_places",
        ),
    )

    def __repr__(self) -> str:
        return f"<Currency {self.code} ({self.symbol})>"
