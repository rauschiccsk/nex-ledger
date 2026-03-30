"""Pydantic schemas pre ImportBatch entity."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImportBatchCreate(BaseModel):
    """Schema pre vytvorenie nového import batchu."""

    filename: str = Field(..., max_length=500, description="Názov importovaného súboru")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash súboru")
    imported_by: str | None = Field(None, max_length=100, description="Kto importoval")

    @field_validator("file_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        """Overenie, že hash je validný SHA256 hex string."""
        if not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("file_hash musí byť validný SHA256 hex string (64 znakov, 0-9a-f)")
        return v.lower()


class ImportBatchRead(BaseModel):
    """Schema pre čítanie import batchu z DB."""

    batch_id: int = Field(..., description="Primárny kľúč")
    filename: str
    file_hash: str
    row_count: int | None
    imported_at: datetime
    imported_by: str | None = Field(None, max_length=100)
    status: str = Field(..., max_length=20, description="Status importu: pending, validated, imported, rejected")
    validation_report: dict[str, Any] | None = Field(None, description="JSON report z validácie")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Overenie, že status je z povolených hodnôt."""
        allowed = {"pending", "validated", "imported", "rejected"}
        if v not in allowed:
            raise ValueError(f"Status musí byť jeden z: {', '.join(allowed)}")
        return v


class ImportBatchUpdate(BaseModel):
    """Schema pre update import batchu (partial update)."""

    row_count: int | None = Field(None, ge=0, description="Počet riadkov v súbore")
    imported_by: str | None = Field(None, max_length=100, description="Kto importoval")
