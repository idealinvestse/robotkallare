"""Helper utilities for call operations."""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session

from app.config import get_settings
from app.models import CallLog, CallRun, Contact, PhoneNumber
from app.services.twilio_call_service import TwilioCallService

logger = logging.getLogger(__name__)
settings = get_settings()


async def wait_for_call_answer(session: Session, call_sid: str, timeout_seconds: int = 30) -> bool:
    """
    Wait for a call to be answered, checking the call status periodically.
    
    Args:
        session: Database session
        call_sid: The Twilio call SID to check
        timeout_seconds: Maximum time to wait for answer
        
    Returns:
        True if the call was answered, False otherwise
    """
    twilio_service = TwilioCallService()
    start_time = datetime.now()
    
    while (datetime.now() - start_time).seconds < timeout_seconds:
        try:
            call_status = twilio_service.get_call_status(call_sid)
            
            if call_status in ["completed", "in-progress"]:
                logger.info(f"Call {call_sid} was answered")
                return True
            elif call_status in ["failed", "busy", "no-answer", "canceled"]:
                logger.info(f"Call {call_sid} was not answered: {call_status}")
                return False
                
            # Wait before checking again
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error checking call status for {call_sid}: {str(e)}")
            return False
    
    logger.warning(f"Call {call_sid} timed out waiting for answer")
    return False


def update_call_run_statistics(session: Session, call_run_id: uuid.UUID) -> None:
    """
    Update the statistics for a call run based on current call logs.
    
    Args:
        session: Database session
        call_run_id: The ID of the call run to update
    """
    try:
        call_run = session.get(CallRun, call_run_id)
        if not call_run:
            logger.error(f"Call run with ID {call_run_id} not found")
            return
        
        # Count calls by status
        from sqlmodel import select, func
        
        # Total calls
        total_calls = session.exec(
            select(func.count(CallLog.id))
            .where(CallLog.call_run_id == call_run_id)
        ).first() or 0
        
        # Answered calls
        answered_calls = session.exec(
            select(func.count(CallLog.id))
            .where(
                (CallLog.call_run_id == call_run_id) & 
                (CallLog.answered == True)
            )
        ).first() or 0
        
        # Failed calls
        failed_calls = session.exec(
            select(func.count(CallLog.id))
            .where(
                (CallLog.call_run_id == call_run_id) & 
                (CallLog.status.in_(["failed", "error", "busy", "no-answer"]))
            )
        ).first() or 0
        
        # Update call run
        call_run.total_calls = total_calls
        call_run.completed_calls = total_calls
        call_run.answered_calls = answered_calls
        call_run.failed_calls = failed_calls
        call_run.updated_at = datetime.now()
        
        # Update status based on progress
        if total_calls == 0:
            call_run.status = "pending"
        elif failed_calls == total_calls:
            call_run.status = "failed"
        elif answered_calls + failed_calls == total_calls:
            call_run.status = "completed"
        else:
            call_run.status = "in_progress"
        
        session.add(call_run)
        session.commit()
        
        logger.debug(f"Updated call run {call_run_id} stats: {total_calls} total, {answered_calls} answered, {failed_calls} failed")
        
    except Exception as e:
        logger.error(f"Error updating call run stats for {call_run_id}: {str(e)}", exc_info=True)


def get_contact_phone_numbers_by_priority(contact: Contact, phone_id: Optional[uuid.UUID] = None) -> List[PhoneNumber]:
    """
    Get phone numbers for a contact, either a specific one or all sorted by priority.
    
    Args:
        contact: Contact object with phone numbers loaded
        phone_id: Optional specific phone number ID to use
        
    Returns:
        List of phone numbers to try, in priority order
    """
    if phone_id:
        # Find specific phone number
        for phone in contact.phone_numbers:
            if phone.id == phone_id:
                return [phone]
        logger.warning(f"Phone number {phone_id} not found for contact {contact.name}")
        return []
    
    # Return all numbers sorted by priority
    return sorted(contact.phone_numbers, key=lambda p: p.priority)


def create_call_log_entry(
    session: Session,
    contact_id: uuid.UUID,
    phone_number_id: uuid.UUID,
    call_sid: str = "pending",
    status: str = "initiated",
    message_id: Optional[uuid.UUID] = None,
    custom_message_log_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None
) -> CallLog:
    """
    Create a new call log entry with proper defaults.
    
    Args:
        session: Database session
        contact_id: ID of the contact being called
        phone_number_id: ID of the phone number being called
        call_sid: Twilio call SID (default: "pending")
        status: Call status (default: "initiated")
        message_id: Optional message ID
        custom_message_log_id: Optional custom message log ID
        call_run_id: Optional call run ID
        
    Returns:
        Created CallLog object
    """
    call_log = CallLog(
        contact_id=contact_id,
        phone_number_id=phone_number_id,
        call_sid=call_sid,
        started_at=datetime.now(),
        answered=False,
        status=status,
        message_id=message_id,
        custom_message_log_id=custom_message_log_id,
        call_run_id=call_run_id
    )
    
    session.add(call_log)
    session.commit()
    session.refresh(call_log)
    
    return call_log


def update_call_log_status(
    session: Session,
    call_log: CallLog,
    status: str,
    call_sid: Optional[str] = None,
    answered: Optional[bool] = None
) -> None:
    """
    Update call log with new status and optional additional information.
    
    Args:
        session: Database session
        call_log: CallLog object to update
        status: New status
        call_sid: Optional new call SID
        answered: Optional answered flag
    """
    try:
        call_log.status = status
        call_log.updated_at = datetime.now()
        
        if call_sid:
            call_log.call_sid = call_sid
            
        if answered is not None:
            call_log.answered = answered
            
        session.add(call_log)
        session.commit()
        
    except Exception as e:
        logger.error(f"Error updating call log {call_log.id}: {str(e)}", exc_info=True)


def validate_call_parameters(
    contact_id: Optional[uuid.UUID] = None,
    message_id: Optional[uuid.UUID] = None,
    phone_id: Optional[uuid.UUID] = None
) -> List[str]:
    """
    Validate call parameters and return list of validation errors.
    
    Args:
        contact_id: Contact ID to validate
        message_id: Message ID to validate
        phone_id: Phone ID to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if not contact_id:
        errors.append("contact_id is required")
    
    if not message_id:
        errors.append("message_id is required")
    
    # Additional validation could be added here
    # e.g., check if IDs exist in database
    
    return errors


async def make_call_with_retry(
    twilio_service: TwilioCallService,
    to_number: str,
    message_id: Optional[uuid.UUID] = None,
    custom_message_id: Optional[uuid.UUID] = None,
    max_retries: int = 3,
    retry_delay: int = 5
) -> Optional[str]:
    """
    Make a call with retry logic for transient failures.
    
    Args:
        twilio_service: Twilio service instance
        to_number: Phone number to call
        message_id: Optional message ID
        custom_message_id: Optional custom message ID
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Call SID if successful, None if failed
    """
    for attempt in range(max_retries + 1):
        try:
            call_sid = twilio_service.make_call(
                to_number=to_number,
                message_id=message_id,
                custom_message_id=custom_message_id
            )
            
            if call_sid:
                logger.info(f"Call successful on attempt {attempt + 1}")
                return call_sid
                
        except Exception as e:
            logger.warning(f"Call attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"All {max_retries + 1} call attempts failed")
    
    return None
