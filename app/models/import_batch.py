"""ImportBatch model — sledovanie dávkových importov dát."""

from enum import StrEnum

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TIMESTAMP

from app.models.base import Base, TimestampMixin, UUIDMixin


class ImportBatchStatus(StrEnum):
    """Status dávkového importu."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def values_callable(cls):
        """Return list of enum values for SQLAlchemy."""
        return [member.value for member in cls]


class ImportBatch(Base, UUIDMixin, TimestampMixin):
    """ImportBatch — záznam o dávkovom importe dát.

    Sleduje priebeh importu vrátane počtu záznamov,
    stavu spracovania a prípadných chybových hlásení.
    """

    __tablename__ = "import_batch"

    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    source_system = Column(String(100))
    file_name = Column(String(255))
    imported_at = Column(TIMESTAMP(timezone=True))
    imported_by = Column(String(100))
    status = Column(
        postgresql.ENUM(
            ImportBatchStatus,
            name="import_batch_status_enum",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    total_records = Column(Integer)
    processed_records = Column(Integer, default=0)
    error_message = Column(Text)

    def __repr__(self) -> str:
        return (
            f"<ImportBatch(batch_number={self.batch_number}, "
            f"status={self.status}, "
            f"processed={self.processed_records}/{self.total_records})>"
        )
