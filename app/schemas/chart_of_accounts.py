"""Pydantic schemas pre ChartOfAccounts entity."""

from pydantic import BaseModel, ConfigDict, Field


class ChartOfAccountsCreate(BaseModel):
    """Schema pre vytvorenie účtového rozvrhu."""

    code: str = Field(..., max_length=20, description="Kód účtového rozvrhu")
    name: str = Field(..., max_length=100, description="Názov účtového rozvrhu")
    description: str | None = Field(None, description="Popis účtového rozvrhu")


class ChartOfAccountsRead(BaseModel):
    """Schema pre čítanie účtového rozvrhu z DB."""

    chart_id: int = Field(..., description="Primárny kľúč účtového rozvrhu")
    code: str = Field(..., description="Kód účtového rozvrhu")
    name: str = Field(..., description="Názov účtového rozvrhu")
    description: str | None = Field(None, description="Popis účtového rozvrhu")

    model_config = ConfigDict(from_attributes=True)


class ChartOfAccountsUpdate(BaseModel):
    """Schema pre aktualizáciu účtového rozvrhu."""

    code: str | None = Field(None, max_length=20, description="Kód účtového rozvrhu")
    name: str | None = Field(None, max_length=100, description="Názov účtového rozvrhu")
    description: str | None = Field(None, description="Popis účtového rozvrhu")
