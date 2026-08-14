"""HEB product enrichment for inventory items

Revision ID: 009
Revises: 008
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("inventory_items", sa.Column("heb_product_name", sa.String(), nullable=True))
    op.add_column("inventory_items", sa.Column("heb_url", sa.String(), nullable=True))
    op.add_column("inventory_items", sa.Column("heb_price", sa.Float(), nullable=True))
    op.add_column("inventory_items", sa.Column("heb_image_url", sa.String(), nullable=True))
    op.add_column("inventory_items", sa.Column("heb_status", sa.String(), nullable=False, server_default=sa.text("'pending'")))
    op.add_column("inventory_items", sa.Column("heb_lookup_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("inventory_items", "heb_lookup_at")
    op.drop_column("inventory_items", "heb_status")
    op.drop_column("inventory_items", "heb_image_url")
    op.drop_column("inventory_items", "heb_price")
    op.drop_column("inventory_items", "heb_url")
    op.drop_column("inventory_items", "heb_product_name")
