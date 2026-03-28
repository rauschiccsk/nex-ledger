"""Create account_type table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-28 08:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Define ENUM types (create_type=False — we manage lifecycle manually)
account_category_enum = PG_ENUM(
    "asset", "liability", "equity", "revenue", "expense",
    name="account_category",
    create_type=False,
)
normal_balance_enum = PG_ENUM(
    "debit", "credit",
    name="normal_balance",
    create_type=False,
)


def upgrade() -> None:
    """Create ENUM types and account_type table."""
    # Create ENUM types explicitly
    op.execute(
        "CREATE TYPE account_category"
        " AS ENUM ('asset', 'liability', 'equity', 'revenue', 'expense')"
    )
    op.execute("CREATE TYPE normal_balance AS ENUM ('debit', 'credit')")

    op.create_table(
        "account_type",
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", account_category_enum, nullable=False),
        sa.Column("normal_balance", normal_balance_enum, nullable=False),
        sa.Column(
            "is_system", sa.Boolean(), server_default="false", nullable=False
        ),
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
        sa.UniqueConstraint("code", name="uq_account_type_code"),
    )


def downgrade() -> None:
    """Drop account_type table and ENUM types."""
    op.drop_table("account_type")
    op.execute("DROP TYPE normal_balance")
    op.execute("DROP TYPE account_category")
