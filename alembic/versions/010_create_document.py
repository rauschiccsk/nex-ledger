"""create document

Revision ID: 010
Revises: 009
Create Date: 2026-03-28 14:53:36.105678

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | Sequence[str] | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM type via raw SQL (avoids double-create with sa.Enum)
    op.execute(
        "CREATE TYPE document_type_enum"
        " AS ENUM ('invoice', 'receipt', 'payment', 'other')"
    )

    # Create table — use postgresql.ENUM with create_type=False
    # to reference the already-created ENUM without re-creating it
    op.create_table(
        "document",
        sa.Column("document_number", sa.String(length=50), nullable=False),
        sa.Column(
            "document_type",
            postgresql.ENUM(
                "invoice",
                "receipt",
                "payment",
                "other",
                name="document_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("document_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("business_partner_id", sa.UUID(), nullable=False),
        sa.Column("journal_entry_id", sa.UUID(), nullable=True),
        sa.Column(
            "amount", sa.Numeric(precision=15, scale=2), nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["business_partner_id"],
            ["business_partner.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["journal_entry_id"],
            ["journal_entry.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_number", name="uq_document_document_number"
        ),
    )

    # Create indexes
    op.create_index(
        "ix_document_document_date", "document", ["document_date"]
    )
    op.create_index(
        "ix_document_business_partner_id",
        "document",
        ["business_partner_id"],
    )
    op.create_index(
        "ix_document_journal_entry_id", "document", ["journal_entry_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_document_journal_entry_id", table_name="document")
    op.drop_index(
        "ix_document_business_partner_id", table_name="document"
    )
    op.drop_index("ix_document_document_date", table_name="document")
    op.drop_table("document")

    document_type_enum = sa.Enum(name="document_type_enum")
    document_type_enum.drop(op.get_bind())
