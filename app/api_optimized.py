import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional
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
from .database import get_session, create_db_and_tables
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

app = FastAPI(title="GDial Emergency Notification System API")

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

@app.on_event("startup")
async def on_startup():
    # Create tables and insert initial data if needed
    create_db_and_tables()
    insert_initial_data()
    
    # Initialize settings
    from .settings import initialize_settings
    initialize_settings()
    
    # Set up scheduled tasks
    from apscheduler.schedulers.background import BackgroundScheduler
    from .tts import clean_audio_cache
    from .services.burn_message_service import BurnMessageService
    
    # Create scheduler for background tasks
    scheduler = BackgroundScheduler()
    
    # Add task to clean up old audio files every hour
    scheduler.add_job(clean_audio_cache, 'interval', hours=1)
    
    # Add task to clean up expired burn messages every hour
    def cleanup_burn_messages():
        from .database import engine
        from sqlmodel import Session
        with Session(engine) as session:
            service = BurnMessageService(session)
            count = service.clean_expired_messages()
            logging.info(f"Scheduled cleanup: Deleted {count} expired or viewed burn messages")
            
    scheduler.add_job(cleanup_burn_messages, 'interval', hours=1)
    
    # Start the scheduler
    scheduler.start()
    
    # Register shutdown event to stop scheduler
    @app.on_event("shutdown")
    def shutdown_scheduler():
        scheduler.shutdown()

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