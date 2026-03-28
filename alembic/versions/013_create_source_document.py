"""create source_document table

Revision ID: 013
Revises: 012
Create Date: 2026-03-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str | Sequence[str] | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create source_document table with RESTRICT FKs and unique constraint."""
    op.execute("""
        CREATE TABLE source_document (
            document_id SERIAL PRIMARY KEY,
            document_type VARCHAR(50) NOT NULL,
            document_number VARCHAR(50) NOT NULL,
            issue_date DATE NOT NULL,
            partner_id INTEGER NOT NULL,
            total_amount NUMERIC(15, 2) NOT NULL,
            currency_code VARCHAR(3) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

            CONSTRAINT uq_document_number
                UNIQUE (document_number),

            CONSTRAINT fk_sd_partner
                FOREIGN KEY (partner_id)
                REFERENCES business_partner(partner_id)
                ON DELETE RESTRICT,

            CONSTRAINT fk_sd_currency
                FOREIGN KEY (currency_code)
                REFERENCES currency(currency_code)
                ON DELETE RESTRICT
        )
    """)


def downgrade() -> None:
    """Drop source_document table."""
    op.execute("DROP TABLE IF EXISTS source_document CASCADE")
