from fastapi.testclient import TestClient
from app.api import app

def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.text == "OK"
