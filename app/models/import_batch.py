"""ImportBatch model — sledovanie importných dávok.

Business rules:
- filename: názov importovaného súboru (napr. 'dennik_2025.xlsx')
- file_hash: SHA-256 hash súboru pre detekciu duplicít
- status: pending → validated → imported | rejected
- validation_report: JSONB s detailami validácie (chyby, varovania)
- row_count: počet spracovaných riadkov
"""

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class ImportBatch(Base):
    """Import batch tracking — one record per file import."""

    __tablename__ = "import_batch"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 = 64 hex chars
    imported_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    imported_by = Column(String(100), nullable=True)
    row_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)
    validation_report = Column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("file_hash", name="uq_import_batch_file_hash"),
        CheckConstraint(
            "status IN ('pending', 'validated', 'imported', 'rejected')",
            name="check_import_batch_status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ImportBatch(id={self.batch_id}, filename='{self.filename}', "
            f"status='{self.status}')>"
        )
