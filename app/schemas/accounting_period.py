"""Pydantic schemas pre AccountingPeriod entity."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class AccountingPeriodCreate(BaseModel):
    """Schema pre vytvorenie nového accounting period."""

    chart_id: int = Field(..., gt=0, description="FK to ChartOfAccounts")
    year: int = Field(..., ge=2000, description="Fiscal year (2000+)")
    period_number: int = Field(..., ge=1, le=13, description="Period number (1-12 monthly, 13 closing)")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")
    is_closed: bool = Field(default=False, description="Whether period is closed for entries")


class AccountingPeriodRead(BaseModel):
    """Schema pre čítanie accounting period z DB."""

    period_id: int
    chart_id: int
    year: int
    period_number: int
    start_date: date
    end_date: date
    is_closed: bool

    model_config = ConfigDict(from_attributes=True)


class AccountingPeriodUpdate(BaseModel):
    """Schema pre update accounting period (všetky polia optional okrem period_id)."""

    chart_id: int | None = Field(None, gt=0, description="FK to ChartOfAccounts")
    year: int | None = Field(None, ge=2000, description="Fiscal year (2000+)")
    period_number: int | None = Field(None, ge=1, le=13, description="Period number (1-12 monthly, 13 closing)")
    start_date: date | None = Field(None, description="Period start date")
    end_date: date | None = Field(None, description="Period end date")
    is_closed: bool | None = Field(None, description="Whether period is closed for entries")
