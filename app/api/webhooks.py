from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlmodel import Session, select
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse

from app.database import get_session
from app.models import CallLog, SmsLog
from app.repositories.call_repository import CallRepository # Assuming repository exists
from app.repositories.sms_repository import SmsRepository # Assuming repository exists
from app.logger import logger

router = APIRouter(tags=["webhooks"])

@router.post("/call-status")
async def handle_call_status(
    request: Request,
    db: Session = Depends(get_session)
):
    """Handle call status updates from Twilio."""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        # Other potential fields: CallDuration, RecordingUrl, etc.

        logger.info(f"Received Twilio call status webhook for CallSid: {call_sid}, Status: {call_status}")

        if not call_sid or not call_status:
            logger.warning("Missing CallSid or CallStatus in Twilio webhook payload")
            # Still return 200 to Twilio, but log the issue
            return VoiceResponse()

        # Use repository to update the CallLog
        call_repo = CallRepository(db)
        call_log = call_repo.get_call_log_by_sid(call_sid) # Need to implement this method

        if not call_log:
            logger.error(f"CallLog not found for CallSid: {call_sid}")
            # Consider raising an error or just returning 200
            return VoiceResponse() # Return 200 OK to Twilio anyway

        # Update status based on Twilio's final states
        # Mapping Twilio statuses: queued, ringing, in-progress, completed, busy, failed, no-answer, canceled
        call_log.status = call_status
        if call_status in ["completed", "busy", "failed", "no-answer", "canceled"]:
            # Mark as answered based on Twilio status (adjust logic as needed)
            # 'completed' usually means answered, others imply not.
            call_log.answered = (call_status == "completed")
            # Potentially update call duration, recording URL etc. here

            db.add(call_log)
            db.commit()
            db.refresh(call_log)
            logger.info(f"Updated CallLog {call_log.id} for CallSid {call_sid} to status: {call_status}, answered: {call_log.answered}")

            # Potentially update CallRun statistics here if call_log.call_run_id exists
            if call_log.call_run_id:
                # Assuming update_call_run_stats exists and handles aggregation
                call_repo.update_call_run_stats(call_log.call_run_id)
                logger.info(f"Updated stats for CallRun {call_log.call_run_id}")

        else:
             logger.info(f"Ignoring intermediate CallStatus '{call_status}' for CallSid {call_sid}")

        # Respond to Twilio
        response = VoiceResponse()
        return response

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
    try:
        form_data = await request.form()
        message_sid = form_data.get("MessageSid")
        message_status = form_data.get("MessageStatus") # delivered, undelivered, failed, sent, sending, etc.
        error_code = form_data.get("ErrorCode") # Present on failure

        logger.info(f"Received Twilio SMS status webhook for MessageSid: {message_sid}, Status: {message_status}")

        if not message_sid or not message_status:
            logger.warning("Missing MessageSid or MessageStatus in Twilio SMS webhook payload")
            return MessagingResponse() # Still return 200 OK to Twilio

        # Use repository to update the SmsLog
        sms_repo = SmsRepository(db)
        sms_log = sms_repo.get_sms_log_by_sid(message_sid) # Need to implement this method

        if not sms_log:
            logger.error(f"SmsLog not found for MessageSid: {message_sid}. This might happen for incoming messages.")
            # If not found, it might be an incoming message or something else.
            # We only care about updating logs for messages we sent.
            return MessagingResponse()

        # Update the log with the final status
        # Twilio final states: delivered, undelivered, failed
        # Intermediate states: accepted, queued, sending, sent
        # We are primarily interested in the final states.
        if message_status in ["delivered", "undelivered", "failed"]:
            sms_log.status = message_status
            # Optionally store error code if failed/undelivered
            if error_code and message_status != "delivered":
                 # You might want a dedicated error_code field in SmsLog
                 # For now, we could potentially append it to the existing status or a notes field
                 logger.warning(f"SMS for MessageSid {message_sid} failed/undelivered. Twilio ErrorCode: {error_code}")
                 # Example: sms_log.status = f"{message_status} (Code: {error_code})"

            db.add(sms_log)
            db.commit()
            db.refresh(sms_log)
            logger.info(f"Updated SmsLog {sms_log.id} for MessageSid {message_sid} to status: {sms_log.status}")
        else:
            logger.info(f"Ignoring intermediate SMS status '{message_status}' for MessageSid {message_sid}")

        # Respond to Twilio
        response = MessagingResponse()
        return response

    except Exception as e:
        logger.error(f"Error processing Twilio SMS status webhook: {e}", exc_info=True)
        # Return 500 but let Twilio know we failed internally
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )
