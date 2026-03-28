"""create journal_line

Revision ID: 009
Revises: 008
Create Date: 2026-03-28 13:57:20.709549

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "journal_line",
        sa.Column("journal_entry_id", sa.UUID(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column(
            "debit_amount",
            sa.Numeric(precision=15, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "credit_amount",
            sa.Numeric(precision=15, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("business_partner_id", sa.UUID(), nullable=True),
        sa.Column("tax_rate_id", sa.UUID(), nullable=True),
        sa.Column("tax_base_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("tax_amount", sa.Numeric(precision=15, scale=2), nullable=True),
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
        sa.CheckConstraint(
            "NOT (debit_amount > 0 AND credit_amount > 0)",
            name="ck_journal_line_debit_or_credit",
        ),
        sa.CheckConstraint(
            "credit_amount >= 0", name="ck_journal_line_credit_non_negative"
        ),
        sa.CheckConstraint(
            "debit_amount >= 0", name="ck_journal_line_debit_non_negative"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["account.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["business_partner_id"], ["business_partner.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["journal_entry_id"], ["journal_entry.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tax_rate_id"], ["tax_rate.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "journal_entry_id", "line_number", name="uq_journal_line_entry_line"
        ),
    )
    # Indexes on FK columns for query performance
    op.create_index(
        "ix_journal_line_journal_entry_id",
        "journal_line",
        ["journal_entry_id"],
    )
    op.create_index(
        "ix_journal_line_account_id",
        "journal_line",
        ["account_id"],
    )
    op.create_index(
        "ix_journal_line_business_partner_id",
        "journal_line",
        ["business_partner_id"],
    )
    op.create_index(
        "ix_journal_line_tax_rate_id",
        "journal_line",
        ["tax_rate_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_journal_line_tax_rate_id", table_name="journal_line")
    op.drop_index("ix_journal_line_business_partner_id", table_name="journal_line")
    op.drop_index("ix_journal_line_account_id", table_name="journal_line")
    op.drop_index("ix_journal_line_journal_entry_id", table_name="journal_line")
    op.drop_table("journal_line")
