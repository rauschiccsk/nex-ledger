"""create journal_entry table

Revision ID: 008
Revises: 007
Create Date: 2026-03-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | Sequence[str] | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Define ENUM type (create_type=False — we manage lifecycle manually)
entry_status_enum = PG_ENUM(
    "draft",
    "posted",
    "cancelled",
    name="entry_status_enum",
    create_type=False,
)


def upgrade() -> None:
    """Create ENUM type and journal_entry table."""
    # Create ENUM type explicitly
    op.execute(
        "CREATE TYPE entry_status_enum"
        " AS ENUM ('draft', 'posted', 'cancelled')"
    )

    op.create_table(
        "journal_entry",
        sa.Column("entry_number", sa.String(length=50), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("import_batch_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            entry_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "posted_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("posted_by", sa.String(length=100), nullable=True),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_journal_entry"),
        sa.UniqueConstraint(
            "entry_number", name="uq_journal_entry_entry_number"
        ),
        sa.ForeignKeyConstraint(
            ["import_batch_id"],
            ["import_batch.id"],
            name="fk_journal_entry_import_batch_id",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_journal_entry_entry_date", "journal_entry", ["entry_date"]
    )
    op.create_index(
        "ix_journal_entry_status", "journal_entry", ["status"]
    )


def downgrade() -> None:
    """Drop journal_entry table and ENUM type."""
    op.drop_index("ix_journal_entry_status")
    op.drop_index("ix_journal_entry_entry_date")
    op.drop_table("journal_entry")
    op.execute("DROP TYPE entry_status_enum")
