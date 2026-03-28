"""create import_batch table

Revision ID: 006
Revises: 005
Create Date: 2026-03-28

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Define ENUM type (create_type=False — we manage lifecycle manually)
batch_status_enum = PG_ENUM(
    "pending",
    "processing",
    "completed",
    "failed",
    name="batch_status_enum",
    create_type=False,
)


def upgrade() -> None:
    """Create ENUM type and import_batch table."""
    # Create ENUM type explicitly
    op.execute(
        "CREATE TYPE batch_status_enum"
        " AS ENUM ('pending', 'processing', 'completed', 'failed')"
    )

    op.create_table(
        "import_batch",
        sa.Column("batch_number", sa.String(length=50), nullable=False),
        sa.Column("source_system", sa.String(length=100), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("imported_by", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            batch_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "total_records", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "processed_records", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_number", name="uq_import_batch_batch_number"),
    )


def downgrade() -> None:
    """Drop import_batch table and ENUM type."""
    op.drop_table("import_batch")
    op.execute("DROP TYPE batch_status_enum")
