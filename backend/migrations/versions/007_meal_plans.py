"""Add meal plans and meal plan entries; allow free-text shopping list rows

Revision ID: 007
Revises: 006
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_meal_plans_week_start", "meal_plans", ["week_start"])

    op.create_table(
        "meal_plan_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("meal_plan_id", sa.String(), sa.ForeignKey("meal_plans.id"), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(), nullable=False),
        sa.Column("recipe_id", sa.String(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("servings_multiplier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_meal_plan_entries_plan", "meal_plan_entries", ["meal_plan_id"])
    op.create_index("ix_meal_plan_entries_date", "meal_plan_entries", ["plan_date"])

    # Shopping list: allow untracked/meal-plan rows (item_id NULL) + free-text name
    op.alter_column("shopping_list_items", "item_id", existing_type=sa.String(), nullable=True)
    op.add_column("shopping_list_items", sa.Column("item_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("shopping_list_items", "item_name")
    op.alter_column("shopping_list_items", "item_id", existing_type=sa.String(), nullable=False)
    op.drop_index("ix_meal_plan_entries_date", table_name="meal_plan_entries")
    op.drop_index("ix_meal_plan_entries_plan", table_name="meal_plan_entries")
    op.drop_table("meal_plan_entries")
    op.drop_index("ix_meal_plans_week_start", table_name="meal_plans")
    op.drop_table("meal_plans")
