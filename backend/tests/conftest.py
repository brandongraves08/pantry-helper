"""Pytest configuration and fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db
from app.db.models import Device
import hashlib

# Create in-memory SQLite database for testing
@pytest.fixture(scope="function")
def db():
    """Create a fresh test database for each test"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    # Create a test device
    test_device = Device(
        id="test-device-001",
        name="Test Camera",
        token_hash=hashlib.sha256(b"test-token").hexdigest(),
    )
    db.add(test_device)
    db.commit()
    
    yield db
    
    db.close()

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with the test database"""
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()
