"""Pydantic schemas pre JournalEntry a JournalEntryLine entities."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ==================== JournalEntryLine Schemas ====================


class JournalEntryLineCreate(BaseModel):
    """Schema pre vytvorenie riadku účtovného zápisu."""

    line_number: int = Field(..., ge=1, description="Poradové číslo riadku v zápise")
    account_id: int = Field(..., gt=0, description="FK na Account")
    partner_id: int | None = Field(None, gt=0, description="FK na BusinessPartner (optional)")
    tax_rate_id: int | None = Field(None, gt=0, description="FK na TaxRate (optional)")
    debit_amount: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Debit suma",
    )
    credit_amount: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Credit suma",
    )
    description: str | None = Field(None, max_length=500, description="Popis riadku")
    currency_code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")


class JournalEntryLineRead(BaseModel):
    """Schema pre čítanie riadku účtovného zápisu z DB."""

    line_id: int
    entry_id: int
    line_number: int
    account_id: int
    partner_id: int | None
    tax_rate_id: int | None
    debit_amount: Decimal
    credit_amount: Decimal
    description: str | None
    currency_code: str

    model_config = ConfigDict(from_attributes=True)


class JournalEntryLineUpdate(BaseModel):
    """Schema pre update riadku účtovného zápisu."""

    account_id: int | None = Field(None, gt=0)
    partner_id: int | None = Field(None, gt=0)
    tax_rate_id: int | None = Field(None, gt=0)
    debit_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    credit_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None = Field(None, max_length=500)
    currency_code: str | None = Field(None, min_length=3, max_length=3)


# ==================== JournalEntry Schemas ====================


class JournalEntryCreate(BaseModel):
    """Schema pre vytvorenie účtovného zápisu (header + lines)."""

    batch_id: int | None = Field(None, gt=0, description="FK na ImportBatch (optional)")
    entry_number: str = Field(..., min_length=1, max_length=50, description="Unikátne číslo dokladu")
    entry_date: date = Field(..., description="Dátum účtovného zápisu")
    description: str | None = Field(None, max_length=1000, description="Popis dokladu")
    created_by: str | None = Field(None, max_length=100, description="Meno/ID používateľa")
    lines: list[JournalEntryLineCreate] = Field(
        ...,
        min_length=2,
        description="Zoznam riadkov dokladu (min. 1 riadok)",
    )


class JournalEntryRead(BaseModel):
    """Schema pre čítanie účtovného zápisu z DB."""

    entry_id: int
    batch_id: int | None
    entry_number: str
    entry_date: date
    description: str | None
    created_by: str | None
    created_at: datetime
    lines: list[JournalEntryLineRead]

    model_config = ConfigDict(from_attributes=True)


class JournalEntryUpdate(BaseModel):
    """Schema pre update účtovného zápisu (len header fields)."""

    entry_date: date | None = None
    description: str | None = Field(None, max_length=1000)
