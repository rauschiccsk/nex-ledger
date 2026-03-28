"""BusinessPartner model — customer/supplier business partner entity."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.journal_line import JournalLine


class BusinessPartner(Base, UUIDMixin, TimestampMixin):
    """Business partner entity (customer, supplier, or both)."""

    __tablename__ = "business_partner"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    street: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_customer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_supplier: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # Relationships
    journal_lines: Mapped[list["JournalLine"]] = relationship(
        "JournalLine",
        back_populates="business_partner",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="business_partner",
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_business_partner_code"),
    )

    def __repr__(self) -> str:
        return f"<BusinessPartner(code={self.code!r}, name={self.name!r})>"
