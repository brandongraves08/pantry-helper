"""Add zones and spatial learning tables

Revision ID: 003
Revises: 002
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Zone definitions for shelf regions
    op.create_table(
        "zones",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("device_id", sa.String(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("expected_item_type", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("device_id", "name", name="uq_zone_device_name"),
    )

    # Learned patterns per zone
    op.create_table(
        "zone_patterns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("zone_id", sa.String(), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("inventory_item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), server_default="0"),
        sa.Column("avg_quantity", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), server_default="0.0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("zone_id", "inventory_item_id", name="uq_zone_pattern"),
    )

    # Zone-linked detections
    op.create_table(
        "zone_detections",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("observation_id", sa.String(), sa.ForeignKey("observations.id"), nullable=False),
        sa.Column("zone_id", sa.String(), sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("detected_class", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bbox_x", sa.Float(), nullable=False),
        sa.Column("bbox_y", sa.Float(), nullable=False),
        sa.Column("bbox_w", sa.Float(), nullable=False),
        sa.Column("bbox_h", sa.Float(), nullable=False),
        sa.Column("inferred_item_id", sa.String(), sa.ForeignKey("inventory_items.id"), nullable=True),
        sa.Column("inference_confidence", sa.Float(), nullable=True),
        sa.Column("is_manual_override", sa.Boolean(), server_default="0"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_zones_device", "zones", ["device_id"])
    op.create_index("ix_zones_active", "zones", ["is_active"])
    op.create_index("ix_zone_patterns_zone", "zone_patterns", ["zone_id"])
    op.create_index("ix_zone_detections_observation", "zone_detections", ["observation_id"])
    op.create_index("ix_zone_detections_zone", "zone_detections", ["zone_id"])


def downgrade() -> None:
    op.drop_index("ix_zone_detections_zone", table_name="zone_detections")
    op.drop_index("ix_zone_detections_observation", table_name="zone_detections")
    op.drop_index("ix_zone_patterns_zone", table_name="zone_patterns")
    op.drop_index("ix_zones_active", table_name="zones")
    op.drop_index("ix_zones_device", table_name="zones")
    op.drop_table("zone_detections")
    op.drop_table("zone_patterns")
    op.drop_table("zones")
