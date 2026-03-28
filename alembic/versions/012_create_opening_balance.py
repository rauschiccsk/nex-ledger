"""create opening_balance table

Revision ID: 012
Revises: 011
Create Date: 2026-03-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: str | Sequence[str] | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create opening_balance table with CASCADE FKs and unique constraint."""
    op.execute("""
        CREATE TABLE opening_balance (
            balance_id SERIAL PRIMARY KEY,
            period_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            credit_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

            CONSTRAINT fk_ob_period
                FOREIGN KEY (period_id)
                REFERENCES accounting_period(period_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_ob_account
                FOREIGN KEY (account_id)
                REFERENCES account(account_id)
                ON DELETE CASCADE,

            CONSTRAINT uq_period_account
                UNIQUE (period_id, account_id)
        )
    """)


def downgrade() -> None:
    """Drop opening_balance table."""
    op.execute("DROP TABLE IF EXISTS opening_balance CASCADE")
