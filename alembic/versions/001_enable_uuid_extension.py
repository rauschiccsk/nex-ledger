"""Enable uuid-ossp extension.

Revision ID: 001
Revises:
Create Date: 2026-03-27 20:52:00.000000
"""

from alembic import op

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable uuid-ossp extension."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')


def downgrade() -> None:
    """Drop uuid-ossp extension."""
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
