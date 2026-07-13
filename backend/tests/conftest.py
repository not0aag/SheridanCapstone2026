import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db


@pytest.fixture()
def client():
    """A TestClient backed by a fresh in-memory SQLite database per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def auth_headers(client):
    """Registers and logs in a driver, returning bearer auth headers."""
    client.post(
        "/users/register",
        json={
            "email": "driver@example.com",
            "password": "hunter2",
            "full_name": "Dana Driver",
            "phone_number": "+15550000000",
        },
    )
    login = client.post(
        "/users/login",
        json={"email": "driver@example.com", "password": "hunter2"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
