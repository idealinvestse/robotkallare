import time
import logging
from sqlmodel import Session, select
from app.models import OutboxJob
from app.queue.rabbitmq import publish_message
from app.texter import _send_sms
from app.config import get_settings
from app.utils.alerting import send_alert_email

logger = logging.getLogger("outbox_worker")

# This should be run as a FastAPI startup event or APScheduler job

def process_outbox_jobs():
    """Process pending OutboxJobs and attempt delivery."""
    with Session(get_settings().DATABASE_URL) as session:
        jobs = session.exec(select(OutboxJob).where(OutboxJob.status == "pending")).all()
        for job in jobs:
            try:
                if job.service == "rabbitmq":
                    ok = publish_message(
                        queue_name=job.payload["queue_name"],
                        message=job.payload["message"],
                        persistent=job.payload.get("persistent", True),
                        session=session  # Don't recursively outbox
                    )
                    if ok:
                        job.status = "sent"
                        session.add(job)
                        continue
                elif job.service == "twilio":
                    sid = _send_sms(
                        to_number=job.payload["to_number"],
                        message_content=job.payload["message_content"],
                        session=session  # Don't recursively outbox
                    )
                    if sid:
                        job.status = "sent"
                        session.add(job)
                        continue
                # Add additional service dispatchers here
                job.attempts += 1
                if job.attempts >= 5:
                    job.status = "failed"
                session.add(job)
            except Exception as e:
                job.attempts += 1
                job.last_error = str(e)
                if job.attempts >= 5:
                    job.status = "failed"
                session.add(job)
        session.commit()

if __name__ == "__main__":
    while True:
        process_outbox_jobs()
        time.sleep(10)
