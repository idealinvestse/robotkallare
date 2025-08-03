from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlmodel import Session, select
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from app.database import get_session
from app.models import CallLog, SmsLog
from app.repositories.call_repository import CallRepository # Assuming repository exists
from app.repositories.sms_repository import SmsRepository # Assuming repository exists
from app.logger import logger
from app.settings import settings, AppSettings

router = APIRouter(tags=["webhooks"])


async def _validate_twilio_request(request: Request) -> bool:
    """Validate Twilio webhook request signature for security.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        bool: True if request is valid, False otherwise
    """
    # Skip validation in development environment
    if getattr(settings, 'ENVIRONMENT', 'development') == 'development':
        logger.debug("Skipping Twilio signature validation in development environment")
        return True
    
    try:
        # Get the Twilio signature from headers
        signature = request.headers.get('X-Twilio-Signature', '')
        if not signature:
            logger.warning("Missing Twilio signature in webhook request headers")
            return False
        
        # Get the request URL
        url = str(request.url)
        
        # Get the request body
        body = await request.body()
        
        # Validate the signature using Twilio's RequestValidator
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        return validator.validate(url, body, signature)
        
    except Exception as e:
        logger.error(f"Error validating Twilio webhook signature: {e}", exc_info=True)
        return False

@router.post("/call-status")
async def handle_call_status(
    request: Request,
    db: Session = Depends(get_session)
):
    """Handle call status updates from Twilio."""
    # Validate Twilio webhook signature for security
    if not await _validate_twilio_request(request):
        logger.warning("Invalid Twilio webhook signature")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature"
        )
    
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        call_duration = form_data.get("CallDuration")
        recording_url = form_data.get("RecordingUrl")
        
        logger.info(f"Received Twilio call status webhook for CallSid: {call_sid}, Status: {call_status}")

        if not call_sid:
            logger.warning("Missing CallSid in Twilio webhook payload")
            # Return 200 to Twilio but log the issue
            return VoiceResponse()
            
        if not call_status:
            logger.warning("Missing CallStatus in Twilio webhook payload")
            # Return 200 to Twilio but log the issue
            return VoiceResponse()

        # Use repository to update the CallLog
        call_repo = CallRepository(db)
        call_log = call_repo.get_call_log_by_sid(call_sid)

        if not call_log:
            logger.warning(f"CallLog not found for CallSid: {call_sid}. This might be an incoming call or a call not initiated by us.")
            # Return 200 OK to Twilio anyway to acknowledge receipt
            return VoiceResponse()

        # Update status based on Twilio's final states
        # Mapping Twilio statuses: queued, ringing, in-progress, completed, busy, failed, no-answer, canceled
        old_status = call_log.status
        call_log.status = call_status
        
        if call_status in ["completed", "busy", "failed", "no-answer", "canceled"]:
            # Mark as answered based on Twilio status
            call_log.answered = (call_status == "completed")
            
            # Update additional fields if available
            if call_duration:
                call_log.duration = int(call_duration)
            if recording_url:
                call_log.recording_url = recording_url

            db.add(call_log)
            db.commit()
            db.refresh(call_log)
            logger.info(f"Updated CallLog {call_log.id} for CallSid {call_sid} from status '{old_status}' to '{call_status}', answered: {call_log.answered}")

            # Update CallRun statistics if call_log.call_run_id exists
            if call_log.call_run_id:
                try:
                    call_repo.update_call_run_stats(call_log.call_run_id)
                    logger.info(f"Updated stats for CallRun {call_log.call_run_id}")
                except Exception as stats_err:
                    logger.error(f"Failed to update CallRun stats for CallRun {call_log.call_run_id}: {stats_err}", exc_info=True)
                    # Don't fail the webhook processing for stats update errors
                    db.rollback()
        else:
            logger.info(f"Received intermediate CallStatus '{call_status}' for CallSid {call_sid}")

        # Respond to Twilio
        response = VoiceResponse()
        return response

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Error processing Twilio call status webhook: {e}", exc_info=True)
        # Don't crash, return 500 but let Twilio know we failed internally
        # Twilio might retry if it gets a 5xx error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )

@router.post("/sms-status")
async def handle_sms_status(
    request: Request,
    db: Session = Depends(get_session)
):
    """Handle SMS status updates (delivery receipts) from Twilio."""
    # Validate Twilio webhook signature for security
    if not await _validate_twilio_request(request):
        logger.warning("Invalid Twilio webhook signature")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature"
        )
    
    try:
        form_data = await request.form()
        message_sid = form_data.get("MessageSid")
        message_status = form_data.get("MessageStatus")
        error_code = form_data.get("ErrorCode")
        error_message = form_data.get("ErrorMessage")

        logger.info(f"Received Twilio SMS status webhook for MessageSid: {message_sid}, Status: {message_status}")

        if not message_sid:
            logger.warning("Missing MessageSid in Twilio SMS webhook payload")
            return MessagingResponse()
            
        if not message_status:
            logger.warning("Missing MessageStatus in Twilio SMS webhook payload")
            return MessagingResponse()

        # Use repository to update the SmsLog
        sms_repo = SmsRepository(db)
        sms_log = sms_repo.get_sms_log_by_sid(message_sid)

        if not sms_log:
            logger.warning(f"SmsLog not found for MessageSid: {message_sid}. This might be an incoming message or SMS not sent by us.")
            return MessagingResponse()

        # Store error details if present
        old_status = sms_log.status
        if error_code:
            sms_log.error_code = error_code
        if error_message:
            sms_log.error_message = error_message
            
        # Update the log with the final status
        if message_status in ["delivered", "undelivered", "failed"]:
            sms_log.status = message_status

            db.add(sms_log)
            db.commit()
            db.refresh(sms_log)
            logger.info(f"Updated SmsLog {sms_log.id} for MessageSid {message_sid} from status '{old_status}' to '{sms_log.status}'")
            
            # Log specific error information
            if message_status in ["undelivered", "failed"]:
                logger.warning(f"SMS for MessageSid {message_sid} {message_status}. Error Code: {error_code}, Error Message: {error_message}")
        else:
            logger.info(f"Received intermediate SMS status '{message_status}' for MessageSid {message_sid}")

        # Respond to Twilio
        response = MessagingResponse()
        return response

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Error processing Twilio SMS status webhook: {e}", exc_info=True)
        # Return 500 but let Twilio know we failed internally
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )
