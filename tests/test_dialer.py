import pytest
from sqlmodel import Session
from app.dialer import _wait_for_answer, _make_call
from app.models import CallLog, Contact, PhoneNumber
from datetime import datetime
import uuid
from unittest.mock import patch

@pytest.mark.asyncio
async def test_wait_for_answer_answered(session: Session):
    sid = "test-sid"
    cl = CallLog(
        id=uuid.uuid4(),
        contact_id=uuid.uuid4(),
        phone_number_id=uuid.uuid4(),
        call_sid=sid,
        started_at=datetime.utcnow(),
        answered=True,
        digits="1",
        status="completed",
    )
    session.add(cl)
    session.commit()
    answered = await _wait_for_answer(session, sid)
    assert answered is True

@pytest.mark.asyncio
async def test_wait_for_answer_no_answer(session: Session):
    sid = "test-sid"
    cl = CallLog(
        id=uuid.uuid4(),
        contact_id=uuid.uuid4(),
        phone_number_id=uuid.uuid4(),
        call_sid=sid,
        started_at=datetime.utcnow(),
        answered=False,
        status="initiated",
    )
    session.add(cl)
    session.commit()
    answered = await _wait_for_answer(session, sid)
    assert answered is False
    from sqlmodel import select
    cl = session.exec(select(CallLog).where(CallLog.call_sid == sid)).first()
    assert cl.status == "initiated"  # Will be updated to no-answer in dialer
