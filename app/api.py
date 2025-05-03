import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, or_
from starlette.responses import FileResponse
from pathlib import Path

# Import phone utilities
from .utils.phone_util import validate_phone_number, format_phone_for_display

# Local application imports
from .database import get_session, create_db_and_tables, engine
from .models.settings import SystemSetting, DtmfSetting, SmsSettings, NotificationSettings
from .twilio_io import build_twiml, validate_twilio_request
from .settings_api import router as settings_router
from .burn_api import router as burn_router
from .api_contacts_groups import router as contacts_groups_router
from .schemas import (
    Stats, 
    ContactResponse, PhoneNumberResponse, CallLogResponse, SmsLogResponse,
    ContactCreate, ContactUpdate, 
    GroupCreate, GroupUpdate, GroupDetailResponse, GroupBrief,
    PhoneNumberCreate, MessageCreate, MessageUpdate, MessageResponse,
    DtmfResponseCreate, DtmfResponseUpdate, DtmfResponseResponse,
    CustomCallRequest, CustomSmsRequest, CustomDtmfResponse,
    ScheduledMessageCreate, ScheduledMessageUpdate, ScheduledMessageResponse,
    CallRunCreate, CallRunUpdate, CallRunResponse, CallRunDetailResponse,
    BurnMessageCreate, BurnMessageResponse, BurnSmsRequest
)

from .models import (
    Message, Contact, PhoneNumber, ContactGroup, GroupContactLink, DtmfResponse,
    SmsLog, CallLog, ScheduledMessage, ScheduledMessageContactLink, CustomMessageLog,
    CallRun, BurnMessage
)

from .insert_data import insert_initial_data
from .settings import initialize_settings
from apscheduler.schedulers.background import BackgroundScheduler
from .tts import clean_audio_cache
from .services.burn_message_service import BurnMessageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic moved from on_startup
    logging.info("Lifespan: Startup sequence initiating...")
    create_db_and_tables()
    logging.info("Lifespan: Database tables checked/created.")
    insert_initial_data()
    logging.info("Lifespan: Initial data checked/inserted.")
    initialize_settings()
    logging.info("Lifespan: Settings initialized.")

    # Scheduler setup
    scheduler = BackgroundScheduler()
    logging.info("Lifespan: Scheduler created.")

    # Add task to clean up old audio files every hour
    scheduler.add_job(clean_audio_cache, 'interval', hours=1)
    logging.info("Lifespan: clean_audio_cache job added.")

    # Add task to clean up expired burn messages every hour
    def cleanup_burn_messages():
        logging.info("Lifespan: Running scheduled cleanup_burn_messages...")
        # Use Session directly from sqlmodel as engine is already imported
        from sqlmodel import Session
        with Session(engine) as session:
            service = BurnMessageService(session)
            count = service.clean_expired_messages()
            logging.info(f"Scheduled cleanup: Deleted {count} expired or viewed burn messages")
            logging.info(f"Lifespan: cleanup_burn_messages finished, deleted {count}.")

    scheduler.add_job(cleanup_burn_messages, 'interval', hours=1)
    logging.info("Lifespan: cleanup_burn_messages job added.")

    # Start the scheduler
    scheduler.start()
    logging.info("Lifespan: Scheduler started.")

    yield # Application runs here

    # Shutdown logic moved from shutdown_scheduler
    logging.info("Lifespan: Shutdown sequence initiating...")
    scheduler.shutdown()
    logging.info("Lifespan: Scheduler shut down.")


app = FastAPI(title="GDial Emergency Notification System API", lifespan=lifespan)

# CORS configuration to allow requests from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(settings_router)
app.include_router(burn_router)
app.include_router(contacts_groups_router)

# Serve static files - single mount point for both paths
app.mount("/ringbot/static", StaticFiles(directory="static"), name="static")

# Add route for serving TTS audio files
@app.get("/ringbot/audio/{file_name}")
async def get_audio_file(file_name: str):
    """Serve a generated audio file for TTS playback."""
    audio_path = Path(f"static/audio/{file_name}")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    media_type = "audio/mpeg" if file_name.endswith(".mp3") else "audio/wav"
    return FileResponse(str(audio_path), media_type=media_type)

# Optimize route handlers using path parameters and route groups
# Define a function to serve HTML files for both root and ringbot paths
def create_html_route_handler(path: str, html_file: str):
    @app.get(f"/{path}", include_in_schema=True)
    @app.get(f"/ringbot/{path}", include_in_schema=True)
    async def serve_html():
        return FileResponse(f"static/{html_file}")
    return serve_html

# Create route handlers
root = create_html_route_handler("", "index.html")
burn_message_page = create_html_route_handler("burn-message", "burn-message.html")
burn_sms_page = create_html_route_handler("burn-sms", "burn-sms.html")
settings_page = create_html_route_handler("settings", "settings.html")

@app.get("/health")
async def health_check(session: Session = Depends(get_session)):
    """Health check endpoint with system status information."""
    health_data = {
        "status": "ok",
        "time": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "connected" if session else "disconnected",
        "api": "running"
    }
    
    # Test database connection
    try:
        # Try a simple query
        session.exec(select(1)).one()
        health_data["database_status"] = "healthy"
    except Exception as e:
        health_data["database_status"] = "error"
        health_data["database_error"] = str(e)
        
    return health_data

# Message endpoints
@app.post("/messages", response_model=MessageResponse, status_code=201)
def create_message(
    message: MessageCreate, session: Session = Depends(get_session)
):
    db_msg = Message(
        name=message.name,
        content=message.content,
        is_template=message.is_template,
        message_type=message.message_type,
    )
    session.add(db_msg)
    session.commit()
    session.refresh(db_msg)
    return db_msg

@app.delete("/messages/{message_id}", status_code=204)
def delete_message(
    message_id: uuid.UUID, session: Session = Depends(get_session)
):
    db_msg = session.exec(select(Message).where(Message.id == message_id)).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Message not found")
    session.delete(db_msg)
    session.commit()
    return Response(status_code=204)