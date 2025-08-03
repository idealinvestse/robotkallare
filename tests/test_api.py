from fastapi.testclient import TestClient
from app.main import app
import uuid
from datetime import datetime
from app.models import Message
from app.schemas import MessageCreate

def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    
    # Parse response to JSON
    data = r.json()
    
    # Check for required fields
    assert "status" in data
    assert "time" in data
    assert "version" in data
    assert "database" in data
    assert "api" in data
    assert "database_status" in data
    
    # Verify values
    assert data["status"] == "ok"
    assert data["api"] == "running"

def test_create_message():
    client = TestClient(app)
    message_data = {
        "name": "Test Message",
        "content": "This is a test message",
        "is_template": True
    }
    
    response = client.post("/messages", json=message_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Message"
    assert data["content"] == "This is a test message"
    assert data["is_template"] == True
    assert "id" in data
    
    # Cleanup - delete the created message
    message_id = data["id"]
    client.delete(f"/messages/{message_id}")
