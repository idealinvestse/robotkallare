import os
import dotenv
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.models import User
from app.database import get_session
from app.main import app
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture(name="session")
def session_fixture(tmp_path):
    # Use tmp_path for SQLite file to avoid Windows file lock and path issues
    db_file = tmp_path / "test.db"
    # Use forward slashes in path
    db_url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def seed_test_user(session):
    user = User(
        username="test",
        email="test@example.com",
        hashed_password=pwd_context.hash("pass"),
        disabled=False,
    )
    session.add(user)
    session.commit()
    return user

def test_login_with_username(client, seed_test_user):
    resp = client.post("/api/v1/auth/login", data={"username": "test", "password": "pass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_with_email(client, seed_test_user):
    resp = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "pass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_wrong_password(client, seed_test_user):
    resp = client.post("/api/v1/auth/login", data={"username": "test", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"

def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", data={"username": "nope", "password": "pass"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"

def test_login_disabled_user(client, session):
    user = User(
        username="disabled",
        email="disabled@example.com",
        hashed_password=pwd_context.hash("pass"),
        disabled=True,
    )
    session.add(user)
    session.commit()
    resp = client.post("/api/v1/auth/login", data={"username": "disabled", "password": "pass"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"
