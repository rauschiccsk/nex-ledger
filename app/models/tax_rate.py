"""TaxRate model — tax rates (VAT, sales tax, etc.).

Business rules:
- code: unique short identifier (e.g., 'VAT20', 'VAT10')
- rate: percentage value 0-100, enforced by CHECK constraint
- valid_from/valid_to: temporal validity (nullable)
- is_active: deactivated rates stay in DB for history
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)

from app.models.base import Base


class TaxRate(Base):
    """Tax rate model (VAT, sales tax, etc.)."""

    __tablename__ = "tax_rate"

    tax_rate_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_tax_rate_code"),
        CheckConstraint("rate >= 0 AND rate <= 100", name="check_rate_range"),
    )

    def __repr__(self) -> str:
        return f"<TaxRate(code='{self.code}', rate={self.rate}%)>"
