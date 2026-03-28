"""create accounting_period table

Revision ID: 008
Revises: 007
Create Date: 2026-03-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | Sequence[str] | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create accounting_period table."""
    op.create_table(
        "accounting_period",
        sa.Column("period_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chart_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("period_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "is_closed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chart_id"],
            ["chart_of_accounts.chart_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("period_id"),
        sa.UniqueConstraint(
            "chart_id",
            "year",
            "period_number",
            name="uq_chart_year_period",
        ),
    )


def downgrade() -> None:
    """Drop accounting_period table."""
    op.drop_table("accounting_period")
