"""Business Partner model for NEX Ledger.

Represents customers, suppliers, or both — obchodný partner.
"""

from sqlalchemy import Boolean, Column, String

from app.models.base import Base, TimestampMixin, UUIDMixin


class BusinessPartner(Base, UUIDMixin, TimestampMixin):
    """Business partner entity — obchodný partner.

    Can be a customer, supplier, or both. Identified by a unique code.
    Examples:
    - code="CUST001", name="Acme Corporation", is_customer=True
    - code="SUPP001", name="Supply Chain Inc.", is_supplier=True
    - code="BOTH001", name="Universal Trading Ltd.", is_customer=True, is_supplier=True
    """

    __tablename__ = "business_partner"

    # Unique identifier
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique business partner code",
    )

    # Basic info
    name = Column(
        String(200),
        nullable=False,
        comment="Business partner name",
    )
    tax_id = Column(
        String(50),
        nullable=True,
        comment="Tax identification number (ICO)",
    )
    vat_id = Column(
        String(50),
        nullable=True,
        comment="VAT identification number (IC DPH)",
    )

    # Address
    street = Column(
        String(200),
        nullable=True,
        comment="Street address",
    )
    city = Column(
        String(100),
        nullable=True,
        comment="City",
    )
    postal_code = Column(
        String(20),
        nullable=True,
        comment="Postal code",
    )
    country_code = Column(
        String(2),
        nullable=True,
        comment="ISO 3166-1 alpha-2 country code",
    )

    # Contact
    email = Column(
        String(100),
        nullable=True,
        comment="Email address",
    )
    phone = Column(
        String(50),
        nullable=True,
        comment="Phone number",
    )

    # Partner role flags
    is_customer = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether the partner is a customer",
    )
    is_supplier = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether the partner is a supplier",
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether the partner is currently active",
    )

    def __repr__(self) -> str:
        return f"<BusinessPartner(code={self.code!r}, name={self.name!r})>"
