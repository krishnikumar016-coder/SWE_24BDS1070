import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_burnout.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_register_login_consent():
    # 1. Register User
    reg_payload = {
        "email": "testuser@company.com",
        "password": "securepassword123",
        "full_name": "Test User",
        "role": "Employee",
        "client_contact_role": True
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["email"] == "testuser@company.com"
    assert user_data["role"] == "Employee"

    # 2. Login
    login_data = {
        "username": "testuser@company.com",
        "password": "securepassword123"
    }
    res = client.post("/api/auth/login", data=login_data)
    assert res.status_code == 200
    token_info = res.json()
    assert "access_token" in token_info
    token = token_info["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get profile /me
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    profile = res.json()
    assert profile["current_consent"] is False  # default opt-out

    # 4. Toggle consent to opt-in
    res = client.post("/api/auth/consent", json={"hr_data_sharing_opt_in": True}, headers=headers)
    assert res.status_code == 200
    consent_res = res.json()
    assert consent_res["hr_data_sharing_opt_in"] is True

    # 5. Check /me again
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["current_consent"] is True

    # 6. Check consent history
    res = client.get("/api/auth/consent-history", headers=headers)
    assert res.status_code == 200
    history = res.json()
    assert len(history) >= 2  # initial + updated
