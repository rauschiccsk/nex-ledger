"""create account table

Revision ID: 009
Revises: 008
Create Date: 2026-03-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create account table with self-FK added after table creation."""
    # Step 1: Create table WITHOUT self-FK (parent_account_id as plain INTEGER)
    op.execute("""
        CREATE TABLE account (
            account_id SERIAL PRIMARY KEY,
            chart_id INTEGER NOT NULL
                REFERENCES chart_of_accounts(chart_id) ON DELETE CASCADE,
            account_number VARCHAR(20) NOT NULL,
            name VARCHAR(200) NOT NULL,
            account_type_id INTEGER NOT NULL
                REFERENCES account_type(account_type_id) ON DELETE RESTRICT,
            currency_code VARCHAR(3) NOT NULL
                REFERENCES currency(currency_code) ON DELETE RESTRICT,
            parent_account_id INTEGER NULL,
            level SMALLINT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            opening_balance NUMERIC(15,2) DEFAULT 0,
            current_balance NUMERIC(15,2) DEFAULT 0,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_chart_account_number UNIQUE (chart_id, account_number)
        )
    """)

    # Step 2: Add self-FK constraint AFTER table exists
    op.execute("""
        ALTER TABLE account
        ADD CONSTRAINT fk_account_parent
        FOREIGN KEY (parent_account_id)
        REFERENCES account(account_id)
        ON DELETE SET NULL
    """)

    # Step 3: Create trigger for updated_at auto-update
    op.execute("""
        CREATE OR REPLACE FUNCTION update_account_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trigger_update_account_updated_at
        BEFORE UPDATE ON account
        FOR EACH ROW
        EXECUTE FUNCTION update_account_updated_at()
    """)


def downgrade() -> None:
    """Drop account table and related objects."""
    # Step 1: Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS trigger_update_account_updated_at ON account")
    op.execute("DROP FUNCTION IF EXISTS update_account_updated_at")

    # Step 2: Drop self-FK constraint BEFORE dropping table
    op.execute("ALTER TABLE account DROP CONSTRAINT IF EXISTS fk_account_parent")

    # Step 3: Drop table
    op.execute("DROP TABLE IF EXISTS account CASCADE")
