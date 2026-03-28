"""ImportBatch model — batch import tracking for data imports."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class BatchStatus(enum.StrEnum):
    """Batch import status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportBatch(Base, UUIDMixin, TimestampMixin):
    """Import batch tracking for data imports."""

    __tablename__ = "import_batch"

    batch_number: Mapped[str] = mapped_column(String(50), nullable=False)
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    imported_by: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        PG_ENUM(
            BatchStatus,
            name="batch_status_enum",
            create_type=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        server_default="pending",
    )
    total_records: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    processed_records: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("batch_number", name="uq_import_batch_batch_number"),
    )

    def __repr__(self) -> str:
        return f"<ImportBatch(batch_number={self.batch_number}, status={self.status.value})>"
