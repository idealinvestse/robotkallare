import uuid
import logging
import json
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
from app.utils.phone_util import validate_phone_number, format_phone_for_display

# Local application imports
from app.database import get_session, create_db_and_tables, engine
from app.settings import SystemSetting, DtmfSetting, SmsSettings, NotificationSettings, settings 
from app.twilio_io import build_twiml, validate_twilio_request
from app.settings_api import router as settings_router
from app.burn_api import router as burn_router
from app.api_contacts_groups import router as contacts_groups_router
from app.api_auth import router as auth_router
from app.api.webhooks import router as webhooks_router
from app.api.outreach import router as outreach_router
from app.realtime.router import router as realtime_router
from app.schemas import (
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

from app.models import (
    Message, Contact, PhoneNumber, ContactGroup, GroupContactLink, DtmfResponse,
    SmsLog, CallLog, ScheduledMessage, ScheduledMessageContactLink, CustomMessageLog,
    CallRun, BurnMessage
)

from app.insert_data import insert_initial_data
from app.settings import initialize_settings
from apscheduler.schedulers.background import BackgroundScheduler
from app.tts import clean_audio_cache
from app.services.burn_message_service import BurnMessageService
from app.repositories.sms_repository_fix import fix_message_by_id_method
from app.publisher import QueuePublisher 

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

    # Apply necessary patches/fixes
    try:
        fix_message_by_id_method()
        logging.info("Lifespan: Applied SmsRepository fix.")
    except Exception as e:
        logging.error(f"Lifespan: Failed to apply SmsRepository fix: {e}", exc_info=True)

    # --- RabbitMQ Setup ---
    rabbitmq_connection = None
    app.state.queue_publisher = None 
    try:
        if not hasattr(settings, 'RABBITMQ_URL') or not settings.RABBITMQ_URL:
             logging.warning("Lifespan: settings.RABBITMQ_URL not defined. Skipping RabbitMQ setup.")
        else:
            logging.info(f"Lifespan: Connecting to RabbitMQ at {settings.RABBITMQ_URL}...")
            rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            rabbitmq_channel = await rabbitmq_connection.channel()
            await rabbitmq_channel.set_qos(prefetch_count=10) 

            exchange = await rabbitmq_channel.declare_exchange(
                "gdial_exchange", aio_pika.ExchangeType.DIRECT, durable=True
            )
            queue = await rabbitmq_channel.declare_queue("gdial.outreach.single", durable=True)
            await queue.bind(exchange, routing_key="outreach.single")

            logging.info(f"Lifespan: RabbitMQ connection, channel, exchange 'gdial_exchange', queue 'gdial.outreach.single' setup complete.")
            app.state.queue_publisher = QueuePublisher(rabbitmq_channel, exchange_name="gdial_exchange")
            logging.info("Lifespan: QueuePublisher stored in app state.")

    except Exception as e:
        logging.error(f"Lifespan: Failed to connect to RabbitMQ or setup publisher: {e}", exc_info=True)
        if rabbitmq_connection and not rabbitmq_connection.is_closed:
             await rabbitmq_connection.close()
        rabbitmq_connection = None 

    # Scheduler setup
    scheduler = BackgroundScheduler()
    logging.info("Lifespan: Scheduler created.")

    # Add task to clean up old audio files every hour
    scheduler.add_job(clean_audio_cache, 'interval', hours=1)
    logging.info("Lifespan: clean_audio_cache job added.")

    # Add task to clean up expired burn messages every hour
    def cleanup_burn_messages():
        logging.info("Lifespan: Running scheduled cleanup_burn_messages...")
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

    yield 

    # Shutdown logic moved from shutdown_scheduler
    logging.info("Lifespan: Shutdown sequence initiating...")
    scheduler.shutdown()
    logging.info("Lifespan: Scheduler shut down.")

    # --- RabbitMQ Shutdown ---
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        logging.info("Lifespan: Closing RabbitMQ connection...")
        await rabbitmq_connection.close()
        logging.info("Lifespan: RabbitMQ connection closed.")
    else:
        logging.info("Lifespan: No active RabbitMQ connection to close.")


app = FastAPI(title="GDial Emergency Notification System API", lifespan=lifespan)

# CORS configuration to allow requests from any origin during development
# CORS configuration - restrict origins in production
# Use CORS_ORIGINS from settings, which can be overridden by environment variables
allowed_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else []

if settings.ENVIRONMENT == "development":
    # In development, allow all origins for easier testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # For production, restrict to known origins from settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

# Mount routers
app.include_router(settings_router)
app.include_router(burn_router)
app.include_router(auth_router)
app.include_router(contacts_groups_router)
app.include_router(webhooks_router)
app.include_router(outreach_router)
app.include_router(realtime_router)

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