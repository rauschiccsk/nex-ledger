"""Pydantic schemas pre AccountType entity."""

from pydantic import BaseModel, ConfigDict, Field


class AccountTypeCreate(BaseModel):
    """Schema pre vytvorenie nového account type."""

    code: str = Field(..., max_length=20, description="Unikátny kód account type")
    name: str = Field(..., max_length=100, description="Názov account type")
    description: str | None = Field(None, description="Popis account type")


class AccountTypeRead(BaseModel):
    """Schema pre čítanie account type z DB."""

    account_type_id: int = Field(..., description="Primárny kľúč")
    code: str
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class AccountTypeUpdate(BaseModel):
    """Schema pre update account type (všetky polia optional)."""

    code: str | None = Field(None, max_length=20)
    name: str | None = Field(None, max_length=100)
    description: str | None = None
