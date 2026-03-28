"""create import_batch table

Revision ID: 005
Revises: 004
Create Date: 2026-03-28 20:11:05.056651

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "import_batch",
        sa.Column("batch_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "imported_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("imported_by", sa.String(length=100), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "validation_report",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'validated', 'imported', 'rejected')",
            name="check_import_batch_status",
        ),
        sa.PrimaryKeyConstraint("batch_id"),
        sa.UniqueConstraint("file_hash", name="uq_import_batch_file_hash"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("import_batch")
