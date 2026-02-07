"""Pytest configuration and fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db
from app.db.models import Device
from app.workers.celery_app import celery_app
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
    
    yield db
    
    db.close()

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with the test database.

    Also forces Celery into eager (in-process) mode so tests don't require
    Redis/rabbitmq.
    """

    # Configure Celery to use an in-memory broker/backend during tests so
    # enqueueing tasks doesn't require Redis/rabbitmq.
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "cache+memory://"
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = True

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
