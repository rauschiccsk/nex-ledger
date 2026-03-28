"""create journal_entry_line table

Revision ID: 011
Revises: 010
Create Date: 2026-03-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: str | Sequence[str] | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create journal_entry_line table with 5 FK constraints."""
    op.execute("""
        CREATE TABLE journal_entry_line (
            line_id SERIAL PRIMARY KEY,
            entry_id INTEGER NOT NULL,
            line_number SMALLINT NOT NULL,
            account_id INTEGER NOT NULL,
            partner_id INTEGER,
            tax_rate_id INTEGER,
            debit_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            credit_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            description TEXT,
            currency_code VARCHAR(3) NOT NULL,

            CONSTRAINT fk_jel_entry
                FOREIGN KEY (entry_id)
                REFERENCES journal_entry(entry_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_jel_account
                FOREIGN KEY (account_id)
                REFERENCES account(account_id)
                ON DELETE RESTRICT,

            CONSTRAINT fk_jel_partner
                FOREIGN KEY (partner_id)
                REFERENCES business_partner(partner_id)
                ON DELETE SET NULL,

            CONSTRAINT fk_jel_tax_rate
                FOREIGN KEY (tax_rate_id)
                REFERENCES tax_rate(tax_rate_id)
                ON DELETE SET NULL,

            CONSTRAINT fk_jel_currency
                FOREIGN KEY (currency_code)
                REFERENCES currency(currency_code)
                ON DELETE RESTRICT,

            CONSTRAINT uq_entry_line_number
                UNIQUE (entry_id, line_number)
        )
    """)


def downgrade() -> None:
    """Drop journal_entry_line table."""
    op.execute("DROP TABLE IF EXISTS journal_entry_line CASCADE")
