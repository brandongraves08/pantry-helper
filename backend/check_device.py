#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.db.database import SessionLocal
from app.db.models import Device, Capture

db = SessionLocal()
device = db.query(Device).filter_by(id='pantry-cam-001').first()
if device:
    print(f'Device: {device.name}')
    print(f'Device ID: {device.id}')
    print(f'Last seen: {device.last_seen_at}')
    if device.last_seen_at:
        print('Status: CONNECTED')
    else:
        print('Status: NOT CONNECTED')
    
    captures = db.query(Capture).filter_by(device_id='pantry-cam-001').count()
    print(f'Captures: {captures}')
else:
    print('Device not found')
db.close()
