import hashlib
from app.db.database import SessionLocal
from app.db.models import Device

db = SessionLocal()

# Delete existing device
existing = db.query(Device).filter_by(id="pantry-cam-001").first()
if existing:
    db.delete(existing)
    db.commit()
    print("Deleted existing device")

# Create new device with new token
token = "iXQfmlnd6n7qO--qFqxd0AX7syxJZHdduZHs1VH-XWI"
token_hash = hashlib.sha256(token.encode()).hexdigest()

device = Device(
    id="pantry-cam-001",
    name="Kitchen Pantry",
    token_hash=token_hash
)
db.add(device)
db.commit()

print(f"Registered device: pantry-cam-001")
print(f"Token: {token}")
print(f"Token hash: {token_hash}")

db.close()
