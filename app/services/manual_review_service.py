from typing import List, Dict, Optional
from uuid import UUID
from sqlmodel import Session
from app.models import OutboxJob, Contact, SmsLog

class OutboxJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def fetch_by_status(self, status: str) -> List[OutboxJob]:
        return self.session.exec(
            OutboxJob.select().where(OutboxJob.status == status)
        ).all()

    def fetch_failed(self) -> List[OutboxJob]:
        return self.fetch_by_status("failed")

    def get_by_id(self, job_id: UUID) -> Optional[OutboxJob]:
        return self.session.get(OutboxJob, job_id)

    def mark_sent(self, job: OutboxJob) -> None:
        job.status = "sent"
        self.session.add(job)
        self.session.commit()

    def mark_failed(self, job: OutboxJob) -> None:
        job.status = "failed"
        self.session.add(job)
        self.session.commit()

    def increment_attempts(self, job: OutboxJob) -> None:
        job.attempts += 1
        self.session.add(job)
        self.session.commit()

class ContactResolver:
    def __init__(self, session: Session):
        self.session = session

    def from_payload(self, payload: dict) -> Optional[Contact]:
        contact_id = payload.get("contact_id")
        phone = payload.get("to_number")
        contact = None
        if contact_id:
            contact = self.session.exec(Contact.select().where(Contact.id == contact_id)).first()
        elif phone:
            sms_log = self.session.exec(SmsLog.select().where(SmsLog.phone_number_id == phone)).first()
            if sms_log:
                contact = self.session.exec(Contact.select().where(Contact.id == sms_log.contact_id)).first()
        return contact

class ManualReviewService:
    def __init__(self, session: Session):
        self.session = session
        self.jobs = OutboxJobRepository(session)
        self.resolver = ContactResolver(session)

    def list_failed_jobs(self, with_contacts: bool = True) -> List[Dict]:
        jobs = self.jobs.fetch_failed()
        results = []
        for job in jobs:
            contact = self.resolver.from_payload(job.payload) if with_contacts else None
            results.append({
                "job_id": str(job.id),
                "service": job.service,
                "payload": job.payload,
                "last_error": job.last_error,
                "attempts": job.attempts,
                "contact": {
                    "id": str(contact.id),
                    "name": contact.name,
                    "email": contact.email,
                    "notes": contact.notes
                } if contact else None
            })
        return results

    def mark_sent(self, job_id: UUID) -> bool:
        job = self.jobs.get_by_id(job_id)
        if not job:
            return False
        self.jobs.mark_sent(job)
        return True

    def mark_failed(self, job_id: UUID) -> bool:
        job = self.jobs.get_by_id(job_id)
        if not job:
            return False
        self.jobs.mark_failed(job)
        return True

    def requeue(self, job_id: UUID) -> bool:
        job = self.jobs.get_by_id(job_id)
        if not job:
            return False
        job.status = "pending"
        job.attempts = 0
        self.session.add(job)
        self.session.commit()
        return True
