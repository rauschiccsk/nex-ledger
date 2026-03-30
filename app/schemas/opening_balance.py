"""Pydantic schemas pre OpeningBalance entity."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OpeningBalanceCreate(BaseModel):
    """Schema pre vytvorenie OpeningBalance záznamu."""

    period_id: int = Field(..., gt=0, description="FK na AccountingPeriod")
    account_id: int = Field(..., gt=0, description="FK na Account")
    debit_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        description="Debit suma v účtovnej mene",
    )
    credit_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        description="Kredit suma v účtovnej mene",
    )


class OpeningBalanceRead(BaseModel):
    """Schema pre čítanie OpeningBalance záznamu."""

    balance_id: int
    period_id: int
    account_id: int
    debit_amount: Decimal
    credit_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpeningBalanceUpdate(BaseModel):
    """Schema pre update OpeningBalance záznamu."""

    debit_amount: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Debit suma v účtovnej mene",
    )
    credit_amount: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Kredit suma v účtovnej mene",
    )
