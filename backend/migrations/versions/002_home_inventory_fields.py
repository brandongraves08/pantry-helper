"""Add home-inventory fields: locations, par levels, shopping list, review queue

Revision ID: 002
Revises: 001
Create Date: 2026-02-07

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Locations (pantry/fridge/freezer + shelves/bins)
    op.create_table(
        "locations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("parent_id", "name", name="uq_locations_parent_name"),
    )

    # Extend inventory_items with metadata (units/category)
    op.add_column("inventory_items", sa.Column("category", sa.String(), nullable=True))
    op.add_column("inventory_items", sa.Column("unit", sa.String(), nullable=True))

    # Extend inventory_state with location + expiry + par level
    op.add_column("inventory_state", sa.Column("location_id", sa.String(), sa.ForeignKey("locations.id"), nullable=True))
    op.add_column("inventory_state", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("inventory_state", sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("inventory_state", sa.Column("par_level", sa.Integer(), nullable=True))

    # Shopping list items (computed or manual)
    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("location_id", sa.String(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("needed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Review queue for camera-driven checks
    op.create_table(
        "inventory_reviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("capture_id", sa.String(), sa.ForeignKey("captures.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),  # pending/approved/rejected
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Helpful indexes
    op.create_index("ix_inventory_state_location", "inventory_state", ["location_id"])
    op.create_index("ix_inventory_state_expires_at", "inventory_state", ["expires_at"])
    op.create_index("ix_shopping_list_unresolved", "shopping_list_items", ["resolved_at"])
    op.create_index("ix_reviews_status", "inventory_reviews", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reviews_status", table_name="inventory_reviews")
    op.drop_index("ix_shopping_list_unresolved", table_name="shopping_list_items")
    op.drop_index("ix_inventory_state_expires_at", table_name="inventory_state")
    op.drop_index("ix_inventory_state_location", table_name="inventory_state")

    op.drop_table("inventory_reviews")
    op.drop_table("shopping_list_items")

    op.drop_column("inventory_state", "par_level")
    op.drop_column("inventory_state", "opened_at")
    op.drop_column("inventory_state", "expires_at")
    op.drop_column("inventory_state", "location_id")

    op.drop_column("inventory_items", "unit")
    op.drop_column("inventory_items", "category")

    op.drop_table("locations")
