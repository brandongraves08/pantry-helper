#!/usr/bin/env python3
"""Seed zone patterns for testing"""
import sys
sys.path.insert(0, '/home/brandon/clawd/pantry-helper/backend')

from app.db.database import SessionLocal
from app.db.models import InventoryItem, Zone, ZonePattern
from datetime import datetime, timezone

session = SessionLocal()

# Find or create 'tomatoes' in inventory
tomato_item = session.query(InventoryItem).filter_by(canonical_name='Tomatoes').first()
if not tomato_item:
    tomato_item = InventoryItem(
        canonical_name='Tomatoes',
        brand='Del Monte',
        package_type='can'
    )
    session.add(tomato_item)
    session.flush()
    print('Created inventory item: Tomatoes')
else:
    print(f'Found inventory item: {tomato_item.canonical_name}')

# Get the zone we created
zone = session.query(Zone).filter_by(name='shelf_3_left').first()
if not zone:
    print('Zone not found!')
    exit(1)

# Seed a pattern: Tomatoes appear in this zone often
existing_pattern = session.query(ZonePattern).filter_by(
    zone_id=zone.id,
    inventory_item_id=tomato_item.id
).first()

if existing_pattern:
    # Boost it
    existing_pattern.occurrence_count = 5
    existing_pattern.avg_quantity = 4.0
    existing_pattern.confidence_score = 0.8
    existing_pattern.last_seen_at = datetime.now(timezone.utc)
    print('Updated existing pattern')
else:
    pattern = ZonePattern(
        zone_id=zone.id,
        inventory_item_id=tomato_item.id,
        occurrence_count=5,
        avg_quantity=4.0,
        confidence_score=0.8,
        last_seen_at=datetime.now(timezone.utc)
    )
    session.add(pattern)
    print('Created new pattern for Tomatoes in shelf_3_left')

session.commit()
session.close()
print('✅ Pattern seeded')
