"""Inventory flags (user-reported item issues)

Revision ID: 010
Revises: 009
Create Date: 2026-08-16

"""
from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_flags",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'open'")),
        sa.Column("resolution_note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventory_flags_item_id"), "inventory_flags", ["item_id"], unique=False)
    op.create_index(op.f("ix_inventory_flags_status"), "inventory_flags", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_flags_status"), table_name="inventory_flags")
    op.drop_index(op.f("ix_inventory_flags_item_id"), table_name="inventory_flags")
    op.drop_table("inventory_flags")
