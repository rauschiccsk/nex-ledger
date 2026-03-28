"""fix currency updated_at timestamp timezone

Revision ID: 007
Revises: 006
Create Date: 2026-03-28 23:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | Sequence[str] | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add timezone to currency.updated_at column."""
    op.alter_column(
        "currency",
        "updated_at",
        type_=sa.TIMESTAMP(timezone=True),
        existing_type=sa.TIMESTAMP(),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )


def downgrade() -> None:
    """Remove timezone from currency.updated_at column."""
    op.alter_column(
        "currency",
        "updated_at",
        type_=sa.TIMESTAMP(),
        existing_type=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
