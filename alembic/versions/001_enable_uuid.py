"""Enable uuid-ossp extension.

Revision ID: 001
Revises:
Create Date: 2026-03-27

Enables the uuid-ossp PostgreSQL extension required for uuid_generate_v4()
server-side UUID generation in primary keys.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable uuid-ossp extension for server-side UUID generation."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')


def downgrade() -> None:
    """Drop uuid-ossp extension."""
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
