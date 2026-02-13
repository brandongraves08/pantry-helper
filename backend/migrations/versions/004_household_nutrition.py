"""Add household members, nutrition, and allergen tracking
Revision ID: 004
Revises: 003
Create Date: 2026-02-12
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Household Members
    op.create_table(
        "household_members",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("relationship", sa.String(), nullable=True),  # self, spouse, child, etc.
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Dietary Restrictions
    op.create_table(
        "dietary_restrictions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("member_id", sa.String(), sa.ForeignKey("household_members.id"), nullable=False),
        sa.Column("restriction_type", sa.String(), nullable=False),  # allergy, intolerance, preference, medical
        sa.Column("allergen", sa.String(), nullable=True),  # peanuts, dairy, gluten, etc.
        sa.Column("severity", sa.String(), nullable=True),  # mild, moderate, severe, life_threatening
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Nutrition Targets per Member
    op.create_table(
        "nutrition_targets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("member_id", sa.String(), sa.ForeignKey("household_members.id"), nullable=False),
        sa.Column("daily_calories", sa.Integer(), nullable=True),
        sa.Column("daily_protein_g", sa.Float(), nullable=True),
        sa.Column("daily_carbs_g", sa.Float(), nullable=True),
        sa.Column("daily_fat_g", sa.Float(), nullable=True),
        sa.Column("daily_fiber_g", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Nutrition Facts per Inventory Item
    op.create_table(
        "nutrition_facts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("inventory_item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("source", sa.String(), nullable=True),  # usda, manual, barcode
        sa.Column("serving_size", sa.String(), nullable=True),  # "1 cup", "100g"
        sa.Column("calories_per_serving", sa.Integer(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("sodium_mg", sa.Float(), nullable=True),
        sa.Column("sugar_g", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Allergens per Inventory Item (Big 9 + custom)
    op.create_table(
        "item_allergens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("inventory_item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("allergen", sa.String(), nullable=False),  # peanuts, tree_nuts, milk, eggs, fish, shellfish, wheat, soy, sesame
        sa.Column("is_present", sa.Boolean(), server_default="1"),  # True=contains, False=may_contain
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("inventory_item_id", "allergen", name="uq_item_allergen"),
    )

    # Consumption Events (who ate what, when)
    op.create_table(
        "consumption_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("member_id", sa.String(), sa.ForeignKey("household_members.id"), nullable=False),
        sa.Column("inventory_item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("quantity_used", sa.Float(), nullable=False),  # servings consumed
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.String(), nullable=True),  # e.g., "breakfast", "snack"
    )

    # Indexes
    op.create_index("ix_household_members_active", "household_members", ["is_active"])
    op.create_index("ix_dietary_restrictions_member", "dietary_restrictions", ["member_id"])
    op.create_index("ix_nutrition_facts_item", "nutrition_facts", ["inventory_item_id"])
    op.create_index("ix_item_allergens_item", "item_allergens", ["inventory_item_id"])
    op.create_index("ix_consumption_member", "consumption_events", ["member_id"])
    op.create_index("ix_consumption_item", "consumption_events", ["inventory_item_id"])
    op.create_index("ix_consumption_date", "consumption_events", ["consumed_at"])


def downgrade() -> None:
    op.drop_index("ix_consumption_date", table_name="consumption_events")
    op.drop_index("ix_consumption_item", table_name="consumption_events")
    op.drop_index("ix_consumption_member", table_name="consumption_events")
    op.drop_index("ix_item_allergens_item", table_name="item_allergens")
    op.drop_index("ix_nutrition_facts_item", table_name="nutrition_facts")
    op.drop_index("ix_dietary_restrictions_member", table_name="dietary_restrictions")
    op.drop_index("ix_household_members_active", table_name="household_members")
    op.drop_table("consumption_events")
    op.drop_table("item_allergens")
    op.drop_table("nutrition_facts")
    op.drop_table("nutrition_targets")
    op.drop_table("dietary_restrictions")
    op.drop_table("household_members")
