"""Test fixtures: every test gets a fresh in-memory SQLite database, so the tests
never touch your real PostgreSQL data and need no running database server."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers tables)
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.security import hash_password


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSession() as db:
        db.add(User(username="tester", full_name="Test User", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # No "with" block: skips the startup hook that would create tables in PostgreSQL
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def auth(client):
    res = client.post("/api/auth/login", json={"username": "tester", "password": "secret123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


FICTIONAL_PATIENT = {
    "full_name": "Rahul Verma",
    "age": 45,
    "gender": "male",
    "phone": "9876501234",
    "email": "rahul.verma@example.com",
    "diagnosis": "Viral fever",
    "symptoms": "Fever and headache",
    "doctor_assigned": "Dr. Kumar",
}
