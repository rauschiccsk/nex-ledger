"""Pydantic schemas pre DocumentEntryLink entity."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentEntryLinkCreate(BaseModel):
    """Schema pre vytvorenie linku medzi dokladom a účtovným záznamom."""

    document_id: int = Field(..., gt=0, description="FK na SourceDocument")
    entry_id: int = Field(..., gt=0, description="FK na JournalEntry")


class DocumentEntryLinkRead(BaseModel):
    """Schema pre čítanie linku medzi dokladom a účtovným záznamom."""

    link_id: int
    document_id: int
    entry_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
