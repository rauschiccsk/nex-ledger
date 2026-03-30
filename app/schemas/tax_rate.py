"""Pydantic schemas pre TaxRate entity."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TaxRateCreate(BaseModel):
    """Schema pre vytvorenie TaxRate entity."""

    code: str = Field(
        ...,
        max_length=20,
        description="Kod danovej sadzby (napr. 'VAT_20', 'VAT_10')",
    )
    name: str = Field(..., max_length=100, description="Nazov danovej sadzby")
    rate: Decimal = Field(
        ...,
        ge=0,
        le=100,
        decimal_places=4,
        description="Danova sadzba v percentach (0.0000 - 100.0000)",
    )
    valid_from: date | None = Field(
        None, description="Datum zaciatku platnosti (ak None, platne od zaciatku)"
    )
    valid_to: date | None = Field(
        None, description="Datum konca platnosti (ak None, platne doteraz)"
    )
    is_active: bool = Field(
        default=True, description="Ci je danova sadzba aktivna"
    )


class TaxRateRead(BaseModel):
    """Schema pre citanie TaxRate entity z DB (ORM mode)."""

    tax_rate_id: int = Field(..., description="Primarny kluc TaxRate entity")
    code: str
    name: str
    rate: Decimal
    valid_from: date | None
    valid_to: date | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TaxRateUpdate(BaseModel):
    """Schema pre update TaxRate entity (vsetky polia optional pre partial update)."""

    code: str | None = Field(None, max_length=20)
    name: str | None = Field(None, max_length=100)
    rate: Decimal | None = Field(None, ge=0, le=100, decimal_places=4)
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool | None = None
