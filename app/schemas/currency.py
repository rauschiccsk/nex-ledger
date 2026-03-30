"""Pydantic schemas pre Currency entity."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CurrencyCreate(BaseModel):
    """Schema pre vytvorenie novej meny."""

    currency_code: str = Field(..., max_length=3, description="ISO 4217 kód meny")
    name: str = Field(..., max_length=100, description="Názov meny")
    symbol: str | None = Field(None, max_length=10, description="Symbol meny (napr. €, $)")
    decimal_places: int = Field(2, ge=0, le=10, description="Počet desatinných miest")
    is_active: bool = Field(True, description="Je mena aktívna?")


class CurrencyRead(BaseModel):
    """Schema pre čítanie meny z DB."""

    currency_code: str
    name: str
    symbol: str | None
    decimal_places: int
    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CurrencyUpdate(BaseModel):
    """Schema pre update meny. Currency_code je path param, ostatné polia optional."""

    name: str | None = Field(None, max_length=100)
    symbol: str | None = Field(None, max_length=10)
    decimal_places: int | None = Field(None, ge=0, le=10)
    is_active: bool | None = None
