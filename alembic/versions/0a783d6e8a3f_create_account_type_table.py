"""Create account_type table

Revision ID: 0a783d6e8a3f
Revises: 00bdf7ca7bbe
Create Date: 2026-03-27 17:36:02.220699

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0a783d6e8a3f'
down_revision: str | Sequence[str] | None = '00bdf7ca7bbe'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create PostgreSQL ENUM types
    account_category_enum = sa.Enum(
        'asset', 'liability', 'equity', 'revenue', 'expense',
        name='account_category_enum',
    )
    account_category_enum.create(op.get_bind(), checkfirst=True)

    normal_balance_enum = sa.Enum(
        'debit', 'credit',
        name='normal_balance_enum',
    )
    normal_balance_enum.create(op.get_bind(), checkfirst=True)

    # Create account_type table
    op.create_table(
        'account_type',
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column(
            'category',
            sa.Enum(
                'asset', 'liability', 'equity', 'revenue', 'expense',
                name='account_category_enum',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            'normal_balance',
            sa.Enum('debit', 'credit', name='normal_balance_enum', create_type=False),
            nullable=False,
        ),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_account_type_code'),
    )
    op.create_index(op.f('ix_account_type_code'), 'account_type', ['code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_account_type_code'), table_name='account_type')
    op.drop_table('account_type')

    # Drop PostgreSQL ENUM types
    sa.Enum(name='normal_balance_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='account_category_enum').drop(op.get_bind(), checkfirst=True)
