"""Pydantic schemas pre SourceDocument entity."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceDocumentCreate(BaseModel):
    """Schema pre vytvorenie source document."""

    document_type: Literal["invoice", "received_invoice", "cash_receipt"] = Field(
        ..., description="Typ dokladu"
    )
    document_number: str = Field(..., max_length=50, description="Číslo dokladu")
    issue_date: date = Field(..., description="Dátum vystavenia")
    partner_id: int = Field(..., gt=0, description="FK na business_partner")
    total_amount: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Celková suma"
    )
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="FK na currency"
    )


class SourceDocumentRead(BaseModel):
    """Schema pre čítanie source document."""

    document_id: int
    document_type: str
    document_number: str
    issue_date: date
    partner_id: int
    total_amount: Decimal
    currency_code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceDocumentUpdate(BaseModel):
    """Schema pre update source document."""

    document_type: Literal["invoice", "received_invoice", "cash_receipt"] | None = None
    document_number: str | None = Field(None, max_length=50)
    issue_date: date | None = None
    partner_id: int | None = Field(None, gt=0)
    total_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    currency_code: str | None = Field(None, min_length=3, max_length=3)
