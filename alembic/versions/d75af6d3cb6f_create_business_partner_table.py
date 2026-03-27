"""Create business_partner table

Revision ID: d75af6d3cb6f
Revises: 0e25eb69840a
Create Date: 2026-03-27 19:17:27.056736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd75af6d3cb6f'
down_revision: Union[str, Sequence[str], None] = '0e25eb69840a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('business_partner',
    sa.Column('code', sa.String(length=50), nullable=False, comment='Unique business partner code'),
    sa.Column('name', sa.String(length=200), nullable=False, comment='Business partner name'),
    sa.Column('tax_id', sa.String(length=50), nullable=True, comment='Tax identification number (ICO)'),
    sa.Column('vat_id', sa.String(length=50), nullable=True, comment='VAT identification number (IC DPH)'),
    sa.Column('street', sa.String(length=200), nullable=True, comment='Street address'),
    sa.Column('city', sa.String(length=100), nullable=True, comment='City'),
    sa.Column('postal_code', sa.String(length=20), nullable=True, comment='Postal code'),
    sa.Column('country_code', sa.String(length=2), nullable=True, comment='ISO 3166-1 alpha-2 country code'),
    sa.Column('email', sa.String(length=100), nullable=True, comment='Email address'),
    sa.Column('phone', sa.String(length=50), nullable=True, comment='Phone number'),
    sa.Column('is_customer', sa.Boolean(), server_default='false', nullable=False, comment='Whether the partner is a customer'),
    sa.Column('is_supplier', sa.Boolean(), server_default='false', nullable=False, comment='Whether the partner is a supplier'),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False, comment='Whether the partner is currently active'),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('business_partner')
