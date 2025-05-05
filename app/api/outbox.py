from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from typing import Optional
from uuid import UUID
from app.config import get_settings
from app.services.manual_review_service import ManualReviewService

router = APIRouter(prefix="/outbox", tags=["outbox"])

def get_service():
    session = Session(get_settings().DATABASE_URL)
    return ManualReviewService(session)

@router.get("/failed")
def get_failed_jobs(service: Optional[str] = None, limit: int = 100, offset: int = 0):
    service_layer = get_service()
    jobs = service_layer.list_failed_jobs()
    # Optionally filter by service
    if service:
        jobs = [j for j in jobs if j['service'] == service]
    return jobs[offset:offset+limit]

@router.post("/{job_id}/mark-sent")
def mark_sent(job_id: UUID):
    service_layer = get_service()
    ok = service_layer.mark_sent(job_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"ok": True}

@router.post("/{job_id}/requeue")
def requeue(job_id: UUID):
    service_layer = get_service()
    ok = service_layer.requeue(job_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"ok": True}
