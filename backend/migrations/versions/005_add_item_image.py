"""Add image_path to inventory_items

Revision ID: 005
Revises: 004
Create Date: 2026-07-10 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inventory_items', sa.Column('image_path', sa.String(), nullable=True))


def downgrade():
    op.drop_column('inventory_items', 'image_path')
