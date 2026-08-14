"""Add rating/favorite to recipes and inventory items

Revision ID: 008
Revises: 007
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column("recipes", sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("inventory_items", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column("inventory_items", sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("inventory_items", "is_favorite")
    op.drop_column("inventory_items", "rating")
    op.drop_column("recipes", "is_favorite")
    op.drop_column("recipes", "rating")
