"""Tax Rate model for NEX Ledger."""

from sqlalchemy import Boolean, CheckConstraint, Column, Date, Numeric, String

from app.models.base import Base, TimestampMixin, UUIDMixin


class TaxRate(Base, UUIDMixin, TimestampMixin):
    """Tax rate entity — sadzba DPH / dane.

    Príklady:
    - code="VAT_20", name="DPH 20%", rate_percent=20.00
    - code="VAT_10", name="DPH 10% (znížená)", rate_percent=10.00
    - code="VAT_0", name="Oslobodené od DPH", rate_percent=0.00
    """

    __tablename__ = "tax_rate"

    code = Column(
        String(20),
        unique=True,
        nullable=False,
        comment="Tax rate identifier (e.g., VAT_20, VAT_21)",
    )
    name = Column(
        String(100),
        nullable=False,
        comment="Descriptive name (e.g., DPH 20%)",
    )
    rate_percent = Column(
        Numeric(5, 2),
        nullable=False,
        comment="Tax rate percentage (0.00 - 100.00)",
    )
    valid_from = Column(
        Date,
        nullable=False,
        comment="Start date of validity",
    )
    valid_to = Column(
        Date,
        nullable=True,
        comment="End date of validity (NULL = unlimited)",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether the tax rate is currently active",
    )

    __table_args__ = (
        CheckConstraint(
            "rate_percent >= 0 AND rate_percent <= 100",
            name="tax_rate_percent_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<TaxRate {self.code} ({self.rate_percent}%)>"
