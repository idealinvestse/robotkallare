from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Sequence
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlmodel import Session, select
from .config import get_settings
from .models import Contact, PhoneNumber, CallLog

settings = get_settings()
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

async def dial_contacts(
    contacts: Sequence[uuid.UUID] | None = None,
) -> None:
    """
    Background task entry point: load contacts in a fresh session and dial each.
    If `contacts` is a sequence of contact IDs, only those will be dialed.
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    from sqlalchemy.orm import selectinload

    with Session(engine) as session:
        # Load contacts (with phone numbers) in this session
        if contacts is None:
            results = session.exec(
                select(Contact).options(selectinload(Contact.phone_numbers))
            )
            to_dial = results.all()
        else:
            results = session.exec(
                select(Contact)
                .where(Contact.id.in_(contacts))
                .options(selectinload(Contact.phone_numbers))
            )
            to_dial = results.all()
        # Dial each contact
        for contact in to_dial:
            await _dial_single_contact(session, contact)

async def _dial_single_contact(session: Session, contact: Contact) -> None:
    # Order numbers by priority
    numbers = sorted(contact.phone_numbers, key=lambda p: p.priority)
    # Skip contacts with no numbers
    if not numbers:
        return
    for idx, phone in enumerate(numbers):
        try:
            sid = _make_call(phone.number)
            log = CallLog(
                contact_id=contact.id,
                phone_number_id=phone.id,
                call_sid=sid,
                started_at=datetime.utcnow(),
                status="initiated",
                answered=False,
            )
            session.add(log)
            session.commit()
            answered = await _wait_for_answer(session, sid)
            if answered:
                return
            # Update log to no-answer
            log.status = "no-answer"
            session.add(log)
            session.commit()
            if idx < len(numbers) - 1:
                await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
        except TwilioRestException as e:
            log = CallLog(
                contact_id=contact.id,
                phone_number_id=phone.id,
                call_sid=f"error-{datetime.utcnow().isoformat()}",
                started_at=datetime.utcnow(),
                status="error",
                answered=False,
            )
            session.add(log)
            session.commit()
            if idx < len(numbers) - 1:
                await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
    # All attempts failed
    session.add(
        CallLog(
            contact_id=contact.id,
            phone_number_id=numbers[-1].id,
            call_sid=f"manual-{datetime.utcnow().isoformat()}",
            started_at=datetime.utcnow(),
            status="manual",
            answered=False,
        )
    )
    session.commit()

def _make_call(to_number: str) -> str:
    call = twilio_client.calls.create(
        to=to_number,
        from_=settings.TWILIO_FROM_NUMBER,
        url=f"http://{settings.API_HOST}:{settings.API_PORT}/voice",
        timeout=settings.CALL_TIMEOUT_SEC,
    )
    return call.sid

async def _wait_for_answer(session: Session, sid: str) -> bool:
    max_attempts = int(settings.CALL_TIMEOUT_SEC / 2) + 1
    for _ in range(max_attempts):
        await asyncio.sleep(2)
        call: CallLog | None = session.exec(
            select(CallLog).where(CallLog.call_sid == sid)
        ).first()
        if call and call.answered:
            return True
    return False
