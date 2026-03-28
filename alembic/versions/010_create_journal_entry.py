"""create journal_entry table

Revision ID: 010
Revises: 009
Create Date: 2026-03-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | Sequence[str] | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create journal_entry table."""
    op.execute("""
        CREATE TABLE journal_entry (
            entry_id SERIAL PRIMARY KEY,
            batch_id INTEGER REFERENCES import_batch(batch_id) ON DELETE SET NULL,
            entry_number VARCHAR(50) NOT NULL,
            entry_date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_by VARCHAR(100),
            CONSTRAINT uq_journal_entry_entry_number UNIQUE (entry_number)
        )
    """)


def downgrade() -> None:
    """Drop journal_entry table."""
    op.execute("DROP TABLE IF EXISTS journal_entry CASCADE")
