"""BusinessPartner model — obchodní partneri (zákazníci a dodávatelia).

Business rules:
- partner_type: CUSTOMER, SUPPLIER, or BOTH (CHECK constraint)
- code: unique identifier for the partner (e.g., CUST001, SUP001)
- is_active: deactivated partners stay in DB for history
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)

from app.models.base import Base


class BusinessPartner(Base):
    """Business partner (customer/supplier) entity."""

    __tablename__ = "business_partner"

    partner_id = Column(Integer, primary_key=True, autoincrement=True)
    partner_type = Column(String(20), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(20), nullable=True)
    vat_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_business_partner_code"),
        CheckConstraint(
            "partner_type IN ('CUSTOMER', 'SUPPLIER', 'BOTH')",
            name="check_partner_type",
        ),
        {"comment": "Business partners (customers and suppliers)"},
    )

    def __repr__(self) -> str:
        return (
            f"<BusinessPartner(id={self.partner_id}, code='{self.code}', "
            f"name='{self.name}', type='{self.partner_type}')>"
        )
