"""API endpoints for burn messages (read-once messages)."""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from pydantic import UUID4

from app.database import get_session
from app.config import get_settings
from app.models import BurnMessage, Contact, ContactGroup
from app.services.burn_message_service import BurnMessageService
from app.schemas import BurnMessageCreate, BurnMessageResponse, BurnSmsRequest, BurnVoiceCallRequest

# Set up logging
logger = logging.getLogger(__name__)
settings = get_settings()

# Create router
router = APIRouter(tags=["burn-messages"])

# HTML template for displaying burn messages
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Säkert Meddelande</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .message-container {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .warning {{
            color: #721c24;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        h1 {{
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Säkert Meddelande</h1>
    </div>
    <div class="message-container">
        <div class="content">{content}</div>
    </div>
    <div class="warning">
        <strong>Varning:</strong> Detta meddelande kommer att raderas när du lämnar sidan. 
        Det kan inte öppnas igen.
    </div>
</body>
</html>
"""


@router.post("/api/burn-messages", response_model=BurnMessageResponse, status_code=201)
async def create_burn_message(
    message: BurnMessageCreate,
    db: Session = Depends(get_session)
):
    """Create a new burn message that can be viewed once and then deleted."""
    service = BurnMessageService(db)
    
    burn_message = service.create_burn_message(
        content=message.content,
        expires_in_hours=message.expires_in_hours
    )
    
    # Return the message with the URL
    return BurnMessageResponse(
        id=burn_message.id,
        token=burn_message.token,
        content=burn_message.content,
        created_at=burn_message.created_at,
        expires_at=burn_message.expires_at,
        viewed=burn_message.viewed
    )
    
@router.get("/burn/{token}", response_class=HTMLResponse)
async def view_burn_message(
    token: str,
    db: Session = Depends(get_session)
):
    """View a burn message. This will mark the message as viewed and it cannot be accessed again."""
    try:
        service = BurnMessageService(db)
        
        # Only retrieve the message without marking it as viewed first
        message_query = db.exec(
            select(BurnMessage).where(BurnMessage.token == token)
        ).first()
        
        if not message_query:
            html_content = HTML_TEMPLATE.format(
                content="Detta meddelande har utgått eller har redan visats."
            )
            return HTMLResponse(content=html_content, status_code=404)
            
        # Check if message has expired
        if message_query.expires_at < datetime.now():
            html_content = HTML_TEMPLATE.format(
                content="Detta meddelande har utgått."
            )
            return HTMLResponse(content=html_content, status_code=404)
            
        # Check if message has already been viewed
        if message_query.viewed:
            html_content = HTML_TEMPLATE.format(
                content="Detta meddelande har redan visats en gång och kan inte visas igen."
            )
            return HTMLResponse(content=html_content, status_code=404)
        
        # Store the content
        message_content = message_query.content
        
        # Try to mark as viewed in a separate try block
        try:
            message_query.viewed = True
            message_query.viewed_at = datetime.now()
            db.add(message_query)
            db.commit()
            logger.info(f"Marked burn message with token {token} as viewed")
        except Exception as mark_error:
            # If marking fails, log but don't stop the message from being displayed
            logger.error(f"Error marking burn message with token {token} as viewed: {str(mark_error)}", exc_info=True)
            db.rollback()
        
        # Return the message content in HTML
        html_content = HTML_TEMPLATE.format(content=message_content)
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error viewing burn message with token {token}: {str(e)}", exc_info=True)
        html_content = HTML_TEMPLATE.format(
            content="Det uppstod ett fel vid hämtning av meddelandet. Kontakta systemadministratören."
        )
        return HTMLResponse(content=html_content, status_code=500)
    
@router.post("/api/burn-sms")
async def send_burn_sms(
    burn_sms: BurnSmsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Send an SMS with a link to a burn message."""
    # Validate inputs
    if not burn_sms.message_content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
        
    if not burn_sms.recipients and not burn_sms.group_id:
        raise HTTPException(status_code=400, detail="Either recipients or group_id must be provided")
    
    # Validate contacts exist
    if burn_sms.recipients:
        for contact_id in burn_sms.recipients:
            contact = db.exec(select(Contact).where(Contact.id == contact_id)).first()
            if not contact:
                raise HTTPException(status_code=404, detail=f"Contact with ID {contact_id} not found")
    
    # Validate group exists
    if burn_sms.group_id:
        group = db.exec(select(ContactGroup).where(ContactGroup.id == burn_sms.group_id)).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with ID {burn_sms.group_id} not found")
    
    # Initialize service
    service = BurnMessageService(db)
    
    # Send in background to avoid blocking
    background_tasks.add_task(
        service.send_burn_message_sms,
        message_content=burn_sms.message_content,
        burn_content=burn_sms.message_content,  # Use same content for both
        recipients=burn_sms.recipients if burn_sms.recipients else None,
        group_id=burn_sms.group_id,
        custom_link_text=burn_sms.custom_link_text,
        expires_in_hours=burn_sms.expires_in_hours,
        base_url=burn_sms.base_url
    )
    
    return {"detail": "Burn message SMS sending initiated"}
    
@router.post("/api/burn-sms/separate-content")
async def send_burn_sms_with_separate_content(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Send an SMS with a link to a burn message, where SMS content and burn content are different."""
    try:
        # Parse request body
        body = await request.json()
        
        # Validate required fields
        required_fields = ["sms_content", "burn_content"]
        for field in required_fields:
            if field not in body or not body[field]:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Extract parameters
        sms_content = body["sms_content"]
        burn_content = body["burn_content"]
        recipients = body.get("recipients", [])
        group_id = body.get("group_id")
        custom_link_text = body.get("custom_link_text")
        expires_in_hours = body.get("expires_in_hours", 24)
        base_url = body.get("base_url")
        
        # Validate we have recipients
        if not recipients and not group_id:
            raise HTTPException(status_code=400, detail="Either recipients or group_id must be provided")
        
        # Initialize service
        service = BurnMessageService(db)
        
        # Send in background
        background_tasks.add_task(
            service.send_burn_message_sms,
            message_content=sms_content,
            burn_content=burn_content,
            recipients=recipients if recipients else None,
            group_id=uuid.UUID(group_id) if group_id else None,
            custom_link_text=custom_link_text,
            expires_in_hours=expires_in_hours,
            base_url=base_url
        )
        
        return {"detail": "Burn message SMS with separate content sending initiated"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending burn SMS: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sending burn SMS: {str(e)}")

@router.post("/api/burn-message-call")
async def initiate_burn_message_call(
    request: BurnVoiceCallRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Initiate voice calls that direct recipients to a burn message."""
    # Validate contacts exist
    if request.recipients:
        for contact_id in request.recipients:
            contact = db.exec(select(Contact).where(Contact.id == contact_id)).first()
            if not contact:
                raise HTTPException(status_code=404, detail=f"Contact with ID {contact_id} not found")
    
    # Validate group exists
    if request.group_id:
        group = db.exec(select(ContactGroup).where(ContactGroup.id == request.group_id)).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with ID {request.group_id} not found")
    
    # Initialize service
    service = BurnMessageService(db)
    
    # Start the call process in the background
    background_tasks.add_task(
        service.initiate_burn_message_call,
        burn_content=request.burn_content,
        intro_message=request.intro_message,
        recipients=request.recipients if request.recipients else None,
        group_id=request.group_id,
        custom_link_text=request.custom_link_text,
        dtmf_digit=request.dtmf_digit,
        dtmf_message=request.dtmf_message,
        expires_in_hours=request.expires_in_hours,
        base_url=request.base_url
    )
    
    return {"detail": "Burn message call initiated"}
    
@router.delete("/api/burn-messages/cleanup")
async def cleanup_burn_messages(
    db: Session = Depends(get_session)
):
    """Clean up expired and viewed burn messages."""
    service = BurnMessageService(db)
    count = service.clean_expired_messages()
    return {"detail": f"Deleted {count} expired or viewed burn messages"}