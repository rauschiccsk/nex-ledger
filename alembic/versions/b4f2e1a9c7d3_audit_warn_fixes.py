"""Audit WARN fixes: drop duplicate index, is_system server_default, timestamptz

Revision ID: b4f2e1a9c7d3
Revises: 0a783d6e8a3f
Create Date: 2026-03-27 20:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b4f2e1a9c7d3'
down_revision: str | Sequence[str] | None = '0a783d6e8a3f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # WARN 3: Drop duplicate unique index on account_type.code
    # (uq_account_type_code UniqueConstraint remains as the canonical constraint)
    op.execute("DROP INDEX IF EXISTS ix_account_type_code")

    # WARN 5: Add server_default to is_system column
    op.alter_column(
        'account_type',
        'is_system',
        server_default=sa.text("false"),
    )

    # WARN 2: Upgrade timestamp columns from TIMESTAMP to TIMESTAMPTZ
    op.alter_column(
        'currency', 'created_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_server_default=sa.text('CURRENT_TIMESTAMP'),
    )
    op.alter_column(
        'currency', 'updated_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_server_default=sa.text('CURRENT_TIMESTAMP'),
    )
    op.alter_column(
        'account_type', 'created_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_server_default=sa.text('CURRENT_TIMESTAMP'),
    )
    op.alter_column(
        'account_type', 'updated_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_server_default=sa.text('CURRENT_TIMESTAMP'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Restore TIMESTAMP (without timezone)
    for table in ('currency', 'account_type'):
        for col in ('created_at', 'updated_at'):
            op.alter_column(
                table, col,
                type_=sa.DateTime(),
                existing_type=sa.DateTime(timezone=True),
                existing_server_default=sa.text('CURRENT_TIMESTAMP'),
            )

    # Remove is_system server_default
    op.alter_column(
        'account_type',
        'is_system',
        server_default=None,
    )

    # Recreate duplicate index
    op.create_index('ix_account_type_code', 'account_type', ['code'], unique=True)
