from sqlmodel import Session, select
from app.models import OutboxJob, Contact, SmsLog
from app.config import get_settings


def get_failed_jobs_with_contacts():
    """
    Returns a list of dicts with OutboxJobs (status='failed') and associated contact info if available.
    """
    results = []
    with Session(get_settings().DATABASE_URL) as session:
        jobs = session.exec(select(OutboxJob).where(OutboxJob.status == "failed")).all()
        for job in jobs:
            contact = None
            # Try to extract contact info from job payload (for Twilio jobs)
            contact_id = job.payload.get("contact_id")
            phone = job.payload.get("to_number")
            if contact_id:
                contact = session.exec(select(Contact).where(Contact.id == contact_id)).first()
            elif phone:
                # Try to find contact by phone number in SmsLog
                sms_log = session.exec(select(SmsLog).where(SmsLog.phone_number_id == phone)).first()
                if sms_log:
                    contact = session.exec(select(Contact).where(Contact.id == sms_log.contact_id)).first()
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

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_failed_jobs_with_contacts())
