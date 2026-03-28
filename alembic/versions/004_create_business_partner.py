"""create business_partner table

Revision ID: 004
Revises: 003
Create Date: 2026-03-28 20:02:15.665357

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "business_partner",
        sa.Column("partner_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("partner_type", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("tax_id", sa.String(length=20), nullable=True),
        sa.Column("vat_number", sa.String(length=20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.CheckConstraint(
            "partner_type IN ('CUSTOMER', 'SUPPLIER', 'BOTH')",
            name="check_partner_type",
        ),
        sa.PrimaryKeyConstraint("partner_id"),
        sa.UniqueConstraint("code", name="uq_business_partner_code"),
        comment="Business partners (customers and suppliers)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("business_partner")
