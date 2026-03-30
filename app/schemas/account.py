"""Pydantic schemas pre Account entity."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    """Schema pre vytvorenie nového Account záznamu."""

    chart_id: int = Field(..., gt=0, description="FK na ChartOfAccounts")
    account_number: str = Field(..., max_length=20, description="Účtový číslo (unique v rámci chart)")
    name: str = Field(..., max_length=200, description="Názov účtu")
    account_type_id: int = Field(..., gt=0, description="FK na AccountType")
    currency_code: str = Field(..., min_length=3, max_length=3, description="FK na Currency (ISO 4217)")
    parent_account_id: int | None = Field(None, gt=0, description="FK na parent Account (self-referential)")
    level: int = Field(..., ge=1, le=10, description="Úroveň v hierarchii (1=root, max 10)")
    is_active: bool = Field(True, description="Je účet aktívny?")
    opening_balance: Decimal = Field(
        default=Decimal("0.00"),
        decimal_places=2,
        description="Počiatočný zostatok",
    )


class AccountRead(BaseModel):
    """Schema pre čítanie Account záznamu z DB."""

    account_id: int
    chart_id: int
    account_number: str
    name: str
    account_type_id: int
    currency_code: str
    parent_account_id: int | None
    level: int
    is_active: bool
    opening_balance: Decimal
    current_balance: Decimal
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountUpdate(BaseModel):
    """Schema pre update existujúceho Account záznamu."""

    name: str | None = Field(None, max_length=200)
    account_type_id: int | None = Field(None, gt=0)
    currency_code: str | None = Field(None, min_length=3, max_length=3)
    parent_account_id: int | None = Field(None, gt=0)
    level: int | None = Field(None, ge=1, le=10)
    is_active: bool | None = None
