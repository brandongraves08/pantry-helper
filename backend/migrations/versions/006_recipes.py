"""Add recipes and recipe ingredients
Revision ID: 006
Revises: 005
Create Date: 2026-08-08
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("prep_time_min", sa.Integer(), nullable=True),
        sa.Column("cook_time_min", sa.Integer(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("recipe_id", sa.String(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("inventory_item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_recipe_ingredients_recipe", "recipe_ingredients", ["recipe_id"])
    op.create_index("ix_recipe_ingredients_item", "recipe_ingredients", ["inventory_item_id"])


def downgrade() -> None:
    op.drop_index("ix_recipe_ingredients_item", table_name="recipe_ingredients")
    op.drop_index("ix_recipe_ingredients_recipe", table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")