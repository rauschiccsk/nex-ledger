"""Pydantic schemas pre BusinessPartner entity."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessPartnerCreate(BaseModel):
    """Schema pre vytvorenie nového business partnera."""

    partner_type: Literal["CUSTOMER", "SUPPLIER", "BOTH"] = Field(
        ...,
        description="Typ partnera: CUSTOMER, SUPPLIER alebo BOTH",
    )
    code: str | None = Field(None, max_length=50, description="Interný kód partnera")
    name: str = Field(..., max_length=200, description="Názov firmy/meno")
    tax_id: str | None = Field(None, max_length=20, description="IČO")
    vat_number: str | None = Field(None, max_length=20, description="IČ DPH")
    address: str | None = Field(None, description="Adresa")
    contact_person: str | None = Field(
        None, max_length=100, description="Kontaktná osoba"
    )
    email: str | None = Field(None, max_length=100, description="Email")
    phone: str | None = Field(None, max_length=50, description="Telefón")
    is_active: bool = Field(True, description="Aktívny záznam")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validácia emailu."""
        if v is not None and "@" not in v:
            raise ValueError("Neplatný email formát")
        return v


class BusinessPartnerRead(BaseModel):
    """Schema pre čítanie business partnera z DB."""

    partner_id: int = Field(..., description="Primárny kľúč")
    partner_type: str
    code: str | None
    name: str
    tax_id: str | None
    vat_number: str | None
    address: str | None
    contact_person: str | None
    email: str | None
    phone: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class BusinessPartnerUpdate(BaseModel):
    """Schema pre update business partnera."""

    partner_type: Literal["CUSTOMER", "SUPPLIER", "BOTH"] | None = None
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=200)
    tax_id: str | None = Field(None, max_length=20)
    vat_number: str | None = Field(None, max_length=20)
    address: str | None = None
    contact_person: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validácia emailu."""
        if v is not None and "@" not in v:
            raise ValueError("Neplatný email formát")
        return v
