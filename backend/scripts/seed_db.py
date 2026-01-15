"""Device seeding and setup script"""

import argparse
import hashlib
import secrets
import sys
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine, Base
from app.db.models import Device

def hash_token(token: str) -> str:
    """Hash a device token using SHA256"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_test_device(db: Session, device_id: str, name: str, token: str) -> Device:
    """Create a test device with the given token"""
    
    # Check if device exists
    existing = db.query(Device).filter_by(id=device_id).first()
    if existing:
        print(f"Device {device_id} already exists")
        return existing
    
    device = Device(
        id=device_id,
        name=name,
        token_hash=hash_token(token),
        created_at=datetime.utcnow(),
    )
    db.add(device)
    db.commit()
    print(f"Created device: {device_id} ({name})")
    print(f"  Token (keep secret): {token}")
    print(f"  Token hash: {device.token_hash}")
    return device

def generate_token() -> str:
    """Generate a random device token"""
    return secrets.token_urlsafe(32)

def setup_database():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")

def seed_test_data():
    """Populate database with test devices"""
    db = SessionLocal()
    try:
        # Create test device 1
        token1 = generate_token()
        create_test_device(
            db,
            device_id="pantry-cam-001",
            name="Kitchen Pantry",
            token=token1
        )
        
        # Create test device 2
        token2 = generate_token()
        create_test_device(
            db,
            device_id="pantry-cam-002",
            name="Garage Storage",
            token=token2
        )
        
        print("\nTest devices created successfully!")
        print("Use the tokens above to authenticate ESP32 requests.")
        
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Setup and seed Pantry Inventory database")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    subparsers.add_parser("setup", help="Initialize database tables")
    
    # Seed command
    subparsers.add_parser("seed", help="Create test devices")
    
    # Add device command
    add_parser = subparsers.add_parser("add-device", help="Add a new device")
    add_parser.add_argument("device_id", help="Device ID")
    add_parser.add_argument("name", help="Device name")
    add_parser.add_argument("--token", help="Device token (generated if not provided)")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup_database()
    elif args.command == "seed":
        setup_database()
        seed_test_data()
    elif args.command == "add-device":
        db = SessionLocal()
        try:
            token = args.token or generate_token()
            create_test_device(db, args.device_id, args.name, token)
        finally:
            db.close()
    elif args.command is None:
        # Default: setup + seed
        setup_database()
        seed_test_data()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
