"""Currency model — mena (EUR, USD, CZK, ...).

Business rules:
- currency_code: ISO 4217 (3-letter code, e.g., EUR, USD)
- decimal_places: počet desatinných miest (EUR=2, JPY=0)
- is_active: deaktivované meny sa nezobrazujú v UI, ale ostávajú v DB kvôli histórii
"""

from sqlalchemy import TIMESTAMP, Boolean, Column, SmallInteger, String, func, text

from app.models.base import Base


class Currency(Base):
    """Currency table — podporované meny."""

    __tablename__ = "currency"

    currency_code = Column(String(3), primary_key=True)  # ISO 4217 (EUR, USD, CZK)
    name = Column(String(100), nullable=False)  # Euro, US Dollar, Czech Koruna
    symbol = Column(String(10))  # €, $, Kč (nullable)
    decimal_places = Column(
        SmallInteger,
        nullable=False,
        server_default=text("2"),
    )
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.clock_timestamp(),
    )

    def __repr__(self):
        return f"<Currency(code={self.currency_code}, name={self.name}, symbol={self.symbol})>"
