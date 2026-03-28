"""create chart_of_accounts table

Revision ID: 006
Revises: 005
Create Date: 2026-03-28 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "chart_of_accounts",
        sa.Column("chart_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("chart_id"),
        sa.UniqueConstraint("code", name="uq_chart_of_accounts_code"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("chart_of_accounts")
