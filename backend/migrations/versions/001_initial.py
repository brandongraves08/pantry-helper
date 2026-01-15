"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2026-01-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables"""
    
    # devices
    op.create_table(
        'devices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_seen_at', sa.DateTime(timezone=True)),
        sa.Column('last_battery_v', sa.Float()),
        sa.Column('last_rssi', sa.Integer()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    
    # captures
    op.create_table(
        'captures',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('trigger_type', sa.String(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('image_path', sa.String(), nullable=False),
        sa.Column('battery_v', sa.Float()),
        sa.Column('rssi', sa.Integer()),
        sa.Column('status', sa.String(), nullable=False, server_default='stored'),
        sa.Column('error_message', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'])
    )
    
    # observations
    op.create_table(
        'observations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('capture_id', sa.String(), nullable=False),
        sa.Column('raw_json', sa.JSON(), nullable=False),
        sa.Column('scene_confidence', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['capture_id'], ['captures.id'])
    )
    
    # inventory_items
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('canonical_name', sa.String(), nullable=False),
        sa.Column('brand', sa.String()),
        sa.Column('package_type', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_name')
    )
    
    # inventory_state
    op.create_table(
        'inventory_state',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('count_estimate', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_seen_at', sa.DateTime(timezone=True)),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('notes', sa.String()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'])
    )
    
    # inventory_events
    op.create_table(
        'inventory_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('capture_id', sa.String()),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('details', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id']),
        sa.ForeignKeyConstraint(['capture_id'], ['captures.id'])
    )


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('inventory_events')
    op.drop_table('inventory_state')
    op.drop_table('inventory_items')
    op.drop_table('observations')
    op.drop_table('captures')
    op.drop_table('devices')
