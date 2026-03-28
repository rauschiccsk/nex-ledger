"""create document_entry_link table

Revision ID: 014
Revises: 013
Create Date: 2026-03-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: str | Sequence[str] | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create document_entry_link table with CASCADE FKs and unique constraint."""
    op.execute("""
        CREATE TABLE document_entry_link (
            link_id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            entry_id INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

            CONSTRAINT fk_del_document
                FOREIGN KEY (document_id)
                REFERENCES source_document(document_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_del_entry
                FOREIGN KEY (entry_id)
                REFERENCES journal_entry(entry_id)
                ON DELETE CASCADE,

            CONSTRAINT uq_document_entry
                UNIQUE (document_id, entry_id)
        )
    """)


def downgrade() -> None:
    """Drop document_entry_link table."""
    op.execute("DROP TABLE IF EXISTS document_entry_link CASCADE")
