"""Create import_batch table

Revision ID: 8e5b895848e7
Revises: d75af6d3cb6f
Create Date: 2026-03-27 19:49:40.920383

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8e5b895848e7'
down_revision: str | Sequence[str] | None = 'd75af6d3cb6f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create PostgreSQL ENUM type via raw SQL
    op.execute(
        "CREATE TYPE import_batch_status_enum AS ENUM "
        "('pending', 'processing', 'completed', 'failed')"
    )

    op.create_table(
        'import_batch',
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('imported_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('imported_by', sa.String(length=100), nullable=True),
        sa.Column(
            'status',
            postgresql.ENUM(
                'pending', 'processing', 'completed', 'failed',
                name='import_batch_status_enum',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('processed_records', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_import_batch_batch_number'),
        'import_batch',
        ['batch_number'],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_import_batch_batch_number'), table_name='import_batch')
    op.drop_table('import_batch')

    # Drop PostgreSQL ENUM type
    op.execute('DROP TYPE IF EXISTS import_batch_status_enum')
