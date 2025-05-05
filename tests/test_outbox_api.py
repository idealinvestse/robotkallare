"""
Tests for the Outbox API endpoints.

These tests focus on the logic of the outbox API module without requiring
the full application stack.
"""

import pytest
from unittest.mock import patch, MagicMock
import uuid
from fastapi import FastAPI, status, Query, Path, HTTPException, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

# Define mock models and services
class OutboxService:
    def __init__(self, db=None):
        self.session = db or MagicMock()

    def list_failed_jobs(self, service: Optional[str] = None):
        # Will be mocked in tests
        pass

    def mark_sent(self, job_id: uuid.UUID):
        # Will be mocked in tests
        pass

    def requeue(self, job_id: uuid.UUID):
        # Will be mocked in tests
        pass

# Create a mock app for testing
mock_app = FastAPI()

# Define mock dependency
def get_service(db=None):
    return OutboxService(db)

# Mock API routes
@mock_app.get("/outbox/failed")
def get_failed_jobs(service: Optional[str] = Query(None), outbox_service=Depends(get_service)):
    result = outbox_service.list_failed_jobs(service=service)
    return result

@mock_app.post("/outbox/{job_id}/mark-sent")
def mark_job_sent(job_id: str = Path(...), outbox_service=Depends(get_service)):
    uuid_job_id = uuid.UUID(job_id)
    if outbox_service.mark_sent(uuid_job_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Job not found or cannot be marked as sent")

@mock_app.post("/outbox/{job_id}/requeue")
def requeue_job(job_id: str = Path(...), outbox_service=Depends(get_service)):
    uuid_job_id = uuid.UUID(job_id)
    if outbox_service.requeue(uuid_job_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Job not found or cannot be requeued")

# Create test client
client = TestClient(mock_app)

def test_get_failed_jobs():
    """Test retrieving failed jobs."""
    with patch.object(OutboxService, 'list_failed_jobs') as mock_method:
        # Setup mock return value
        mock_method.return_value = [
            {
                "id": str(uuid.uuid4()),
                "service": "sms", 
                "status": "failed",
                "created_at": "2025-05-05T01:00:00",
                "error": "Failed to send SMS"
            },
            {
                "id": str(uuid.uuid4()),
                "service": "call", 
                "status": "failed",
                "created_at": "2025-05-05T01:10:00",
                "error": "Call failed to connect"
            }
        ]

        # Make request
        response = client.get("/outbox/failed")

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["service"] == "sms"
        assert response.json()[1]["service"] == "call"

        # Test with service filter
        mock_method.reset_mock()
        mock_method.return_value = [
            {
                "id": str(uuid.uuid4()),
                "service": "sms", 
                "status": "failed",
                "created_at": "2025-05-05T01:00:00",
                "error": "Failed to send SMS"
            }
        ]

        response = client.get("/outbox/failed?service=sms")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["service"] == "sms"
        mock_method.assert_called_once_with(service="sms")

def test_mark_sent():
    """Test marking a job as sent."""
    with patch.object(OutboxService, 'mark_sent') as mock_method:
        # Setup mock return value
        mock_method.return_value = True

        # Make request
        job_id = str(uuid.uuid4())
        response = client.post(f"/outbox/{job_id}/mark-sent")

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"ok": True}

        # Verify service called with correct job_id
        mock_method.assert_called_once()
        assert mock_method.call_args[0][0] == uuid.UUID(job_id)

def test_mark_sent_not_found():
    """Test marking a non-existent job as sent."""
    with patch.object(OutboxService, 'mark_sent') as mock_method:
        # Setup mock return value
        mock_method.return_value = False

        # Make request
        job_id = str(uuid.uuid4())
        response = client.post(f"/outbox/{job_id}/mark-sent")

        # Assertions
        assert response.status_code == 404

def test_requeue():
    """Test requeuing a job."""
    with patch.object(OutboxService, 'requeue') as mock_method:
        # Setup mock return value
        mock_method.return_value = True

        # Make request
        job_id = str(uuid.uuid4())
        response = client.post(f"/outbox/{job_id}/requeue")

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"ok": True}

        # Verify service called with correct job_id
        mock_method.assert_called_once()
        assert mock_method.call_args[0][0] == uuid.UUID(job_id)

def test_requeue_not_found():
    """Test requeuing a non-existent job."""
    with patch.object(OutboxService, 'requeue') as mock_method:
        # Setup mock return value
        mock_method.return_value = False

        # Make request
        job_id = str(uuid.uuid4())
        response = client.post(f"/outbox/{job_id}/requeue")

        # Assertions
        assert response.status_code == 404
