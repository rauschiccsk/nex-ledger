"""SourceDocument model — prvotné doklady (faktúry, pokladničné doklady).

Business rules:
- document_type: typ dokladu (issued_invoice, received_invoice, cash_receipt)
- document_number: unikátne číslo dokladu (číslo faktúry / pokladničného dokladu)
- issue_date: dátum vystavenia dokladu
- partner_id: FK → business_partner (RESTRICT — nemožno zmazať partnera s dokladmi)
- total_amount: celková suma dokladu (NUMERIC(15,2))
- currency_code: FK → currency (RESTRICT — nemožno zmazať menu s dokladmi)
- created_at: automatický timestamp vytvorenia záznamu
"""

from sqlalchemy import (
    TIMESTAMP,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)

from app.models.base import Base


class SourceDocument(Base):
    """Source document (prvotný doklad) entity.

    Represents invoices, cash receipts, and other primary accounting documents
    that serve as the basis for journal entries and cross-validation.

    Attributes:
        document_id: Primary key (SERIAL)
        document_type: Document type (issued_invoice, received_invoice, cash_receipt)
        document_number: Unique document number
        issue_date: Document issue date
        partner_id: FK to business_partner (RESTRICT delete)
        total_amount: Total document amount
        currency_code: FK to currency (RESTRICT delete)
        created_at: Timestamp of record creation (auto-set by DB)
    """

    __tablename__ = "source_document"

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    document_type = Column(String(50), nullable=False)
    document_number = Column(String(50), nullable=False)
    issue_date = Column(Date, nullable=False)
    partner_id = Column(
        Integer,
        ForeignKey("business_partner.partner_id", ondelete="RESTRICT"),
        nullable=False,
    )
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency_code = Column(
        String(3),
        ForeignKey("currency.currency_code", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("document_number", name="uq_document_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<SourceDocument(document_id={self.document_id}, "
            f"document_number='{self.document_number}', "
            f"document_type='{self.document_type}')>"
        )
