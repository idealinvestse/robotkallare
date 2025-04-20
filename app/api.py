from fastapi import FastAPI, Depends, Request, Response, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import CallLog, Contact
from .twilio_io import build_twiml, validate_twilio_request
from .schemas import Stats
from .dialer import dial_contacts

app = FastAPI(on_startup=[create_db_and_tables])

@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "OK"

@app.post("/voice", response_class=Response)
async def voice(request: Request) -> Response:
    body = await request.body()
    validate_twilio_request(request, body)
    # Return TwiML as XML
    xml = build_twiml()
    return Response(content=xml, media_type="application/xml")

@app.post("/dtmf", response_class=PlainTextResponse)
async def dtmf(request: Request, db: Session = Depends(get_session)) -> str:
    body = await request.body()
    validate_twilio_request(request, body)
    form = await request.form()
    sid = form.get("CallSid")
    digits = form.get("Digits")
    log = db.exec(select(CallLog).where(CallLog.call_sid == sid)).first()
    if log and digits in ["1", "2", "3"]:
        log.answered = True
        log.digits = digits
        log.status = "completed"
        db.add(log)
        db.commit()
    return ""

@app.get("/stats", response_model=Stats)
async def stats(db: Session = Depends(get_session)):
    total_calls = db.exec(select(CallLog)).all()
    completed = len([log for log in total_calls if log.status == "completed"])
    no_answer = len([log for log in total_calls if log.status == "no-answer"])
    manual = len([log for log in total_calls if log.status == "manual"])
    error = len([log for log in total_calls if log.status == "error"])
    last = db.exec(select(CallLog).order_by(CallLog.started_at.desc())).first()
    return Stats(
        total_calls=len(total_calls),
        completed=completed,
        no_answer=no_answer,
        manual=manual,
        error=error,
        last_call=last.started_at if last else None,
    )

@app.post("/trigger-dialer", status_code=202)
async def trigger_dialer(
    bg: BackgroundTasks
) -> dict[str, str]:
    """
    Kick off the dialer in the background using a fresh DB session.
    """
    bg.add_task(dial_contacts)
    return {"detail": "dialer started in background"}
