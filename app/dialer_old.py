"""Legacy dialer module - DEPRECATED.

This module is being refactored. New code should use:
- app.services.dialer_service.DialerService for high-level call operations
- app.services.call_service.CallService for call management
- app.workers.call_worker for background call processing
- app.utils.call_helpers for utility functions

This file is kept for backward compatibility during the transition.
"""
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Sequence, Optional, Dict, Any, List
from sqlmodel import Session

from app.services.dialer_service import DialerService
from app.services.call_service import CallService
from app.dependencies.container import get_container
from app.models import Contact, Message, CallRun

logger = logging.getLogger(__name__)

# Deprecation warning
logger.warning(
    "dialer.py is deprecated. Use app.services.dialer_service.DialerService instead. "
    "This module will be removed in a future version."
)

class DialerService:
    """Legacy DialerService - DEPRECATED wrapper around new architecture."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        logger.warning("DialerService class is deprecated. Use app.services.dialer_service.DialerService instead.")
        self.session = session
        # Use new service architecture
        from app.services.dialer_service import DialerService as NewDialerService
        self._new_service = NewDialerService(session)
    
    async def start_call_run(
        self, 
        contacts: List[uuid.UUID] = None,
        message = None,
        group_id: Optional[uuid.UUID] = None,
        name: str = "Call Run",
        description: Optional[str] = None,
        dtmf_confirmations: bool = False,
        custom_data: Optional[Dict[str, Any]] = None,
        sms_after_dtmf: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Deprecated wrapper - delegates to new DialerService."""
        return await self._new_service.start_call_run(
            contacts=contacts,
            message=message,
            group_id=group_id,
            name=name,
            description=description,
            dtmf_confirmations=dtmf_confirmations,
            custom_data=custom_data,
            sms_after_dtmf=sms_after_dtmf
        )
    
    async def dial_contact(self, contact_id: uuid.UUID, message_id: uuid.UUID, burn_message_token: Optional[str] = None) -> bool:
        """Deprecated wrapper - delegates to new DialerService."""
        return await self._new_service.dial_contact(
            contact_id=contact_id,
            message_id=message_id,
            burn_message_token=burn_message_token
        )
        # Load the contact with phone numbers
        contact = self.session.exec(
            select(Contact)
            .where(Contact.id == contact_id)
            .options(selectinload(Contact.phone_numbers))
        ).first()
        
        if not contact:
            logger.error(f"Contact with ID {contact_id} not found")
            return False
            
        if not contact.phone_numbers:
            logger.error(f"Contact {contact.name} has no phone numbers")
            return False
            
        # Order phone numbers by priority
        phone_numbers = sorted(contact.phone_numbers, key=lambda p: p.priority)
        
        # Try to dial the contact using the global dial_contacts function
        try:
            logger.info(f"Dialing contact {contact.name} with message ID {message_id}")
            
            # Create parameters for the call URL
            params = f"message_id={message_id}"
            if burn_message_token:
                params += f"&burn_token={burn_message_token}"
                
            # Make the call using the existing function
            await dial_contacts(
                contacts=[contact_id],
                message_id=message_id
            )
            
            return True
        except Exception as e:
            logger.error(f"Error dialing contact {contact.name}: {str(e)}", exc_info=True)
            return False

async def dial_contacts(
    contacts: Sequence[uuid.UUID] | None = None,
    group_id: Optional[uuid.UUID] = None,
    message_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None,
    call_run_name: Optional[str] = None,
    call_run_description: Optional[str] = None,
) -> Optional[uuid.UUID]:
    """
    Background task entry point: load contacts in a fresh session and dial each using multiple bots.
    
    Parameters:
    - contacts: If provided, only these specific contact IDs will be dialed
    - group_id: If provided, only contacts in this group will be dialed
    - message_id: If provided, this message will be used for the calls
    - call_run_id: If provided, attach calls to this call run
    - call_run_name: If provided and call_run_id is None, create a new call run with this name
    - call_run_description: Optional description for the new call run
    
    Note: If both contacts and group_id are provided, contacts parameter takes precedence
    
    Returns:
    - The ID of the call run if created, None otherwise
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    from .settings import get_system_setting

    with Session(engine) as session:
        # Get settings for multi-bot configuration
        bot_count = get_system_setting(session, "call_bots_count", 3)
        # Convert to int if it's a string
        if isinstance(bot_count, str):
            bot_count = int(bot_count)
        
        # Load contacts (with phone numbers) in this session
        if contacts is not None:
            # Specific contacts requested
            results = session.exec(
                select(Contact)
                .where(Contact.id.in_(contacts))
                .options(selectinload(Contact.phone_numbers))
            )
            to_dial = results.all()
        elif group_id is not None:
            # Filter by group
            contact_links = session.exec(
                select(GroupContactLink).where(GroupContactLink.group_id == group_id)
            ).all()
            contact_ids = [link.contact_id for link in contact_links]
            
            if contact_ids:
                results = session.exec(
                    select(Contact)
                    .where(Contact.id.in_(contact_ids))
                    .options(selectinload(Contact.phone_numbers))
                )
                to_dial = results.all()
            else:
                to_dial = []
        else:
            # All contacts
            results = session.exec(
                select(Contact).options(selectinload(Contact.phone_numbers))
            )
            to_dial = results.all()
        
        # Create or get a call run
        call_run = None
        if call_run_id:
            # Use existing call run
            call_run = session.exec(select(CallRun).where(CallRun.id == call_run_id)).first()
            if not call_run:
                logger.error(f"Call run with ID {call_run_id} not found")
                return None
        elif call_run_name:
            # Create a new call run
            call_run = CallRun(
                name=call_run_name,
                description=call_run_description,
                message_id=message_id,
                group_id=group_id,
                status="in_progress",
                total_calls=len(to_dial),
                started_at=datetime.now()
            )
            session.add(call_run)
            session.commit()
            session.refresh(call_run)
            logger.info(f"Created new call run: {call_run.name} (ID: {call_run.id})")
        
        # Split contacts among bots for parallel dialing
        try:
            # Use bot_count to distribute the contacts
            # Convert bot_count to int if it's a string
            if isinstance(bot_count, str):
                bot_count = int(bot_count)
                
            num_bots = min(bot_count, len(to_dial))
            
            if num_bots <= 1:
                # If only one bot or few contacts, use the traditional approach
                logger.info(f"Using a single bot for {len(to_dial)} contacts")
                for contact in to_dial:
                    await _dial_single_contact(session, contact, message_id, call_run.id if call_run else None)
            else:
                # Split the contacts among multiple bots
                logger.info(f"Distributing {len(to_dial)} contacts among {num_bots} bots")
                bot_contact_lists = [[] for _ in range(num_bots)]
                
                # Distribute contacts evenly among bots
                for idx, contact in enumerate(to_dial):
                    bot_idx = idx % num_bots
                    bot_contact_lists[bot_idx].append(contact)
                
                # Create and run tasks for each bot
                bot_tasks = []
                for bot_idx, bot_contacts in enumerate(bot_contact_lists):
                    if not bot_contacts:
                        continue
                    logger.info(f"Bot {bot_idx+1} is handling {len(bot_contacts)} contacts")
                    bot_task = asyncio.create_task(
                        _bot_dial_contacts(
                            session.engine,
                            bot_contacts,
                            message_id, 
                            call_run.id if call_run else None,
                            bot_idx
                        )
                    )
                    bot_tasks.append(bot_task)
                
                # Wait for all bots to complete their work
                if bot_tasks:
                    await asyncio.gather(*bot_tasks)
            
            # Update call run if it exists
            if call_run:
                # Get updated counts
                total_calls = session.exec(
                    select(CallLog).where(CallLog.call_run_id == call_run.id)
                ).count()
                completed_calls = session.exec(
                    select(CallLog).where(
                        (CallLog.call_run_id == call_run.id) & 
                        (CallLog.status.in_(["completed", "no-answer", "manual", "error"]))
                    )
                ).count()
                answered_calls = session.exec(
                    select(CallLog).where(
                        (CallLog.call_run_id == call_run.id) & 
                        (CallLog.answered == True)
                    )
                ).count()
                
                # Update the call run
                call_run.total_calls = total_calls
                call_run.completed_calls = completed_calls
                call_run.answered_calls = answered_calls
                
                # If all calls are completed, mark the call run as completed
                if completed_calls == total_calls:
                    call_run.status = "completed"
                    call_run.completed_at = datetime.now()
                
                session.add(call_run)
                session.commit()
                logger.info(f"Updated call run: {call_run.name} (ID: {call_run.id})")
                
            return call_run.id if call_run else None
        except Exception as e:
            logger.error(f"Unexpected error in dial_contacts: {str(e)}", exc_info=True)
            return None

async def _bot_dial_contacts(
    engine,
    contacts: List[Contact],
    message_id: Optional[uuid.UUID],
    call_run_id: Optional[uuid.UUID],
    bot_id: int
) -> None:
    """
    Worker function for a single bot to dial its assigned contacts.
    
    Parameters:
    - engine: SQLAlchemy engine to create a session
    - contacts: List of contacts this bot is responsible for
    - message_id: Optional message ID to use for calls
    - call_run_id: Optional call run ID to associate with these calls
    - bot_id: ID of this bot for logging purposes
    """
    # Create a new session for this bot
    from sqlmodel import Session
    from .settings import get_system_setting
    
    logger.info(f"Bot {bot_id} starting to dial {len(contacts)} contacts")
    
    with Session(engine) as bot_session:
        # Get the calls_per_bot setting
        calls_per_bot = get_system_setting(bot_session, "calls_per_bot", 20)
        # Convert to int if it's a string
        if isinstance(calls_per_bot, str):
            calls_per_bot = int(calls_per_bot)
        
        # Create a semaphore to limit concurrent calls per bot
        semaphore = asyncio.Semaphore(calls_per_bot)
        
        # Create tasks for each contact and run them with the semaphore
        async def dial_with_semaphore(contact):
            async with semaphore:
                return await _dial_single_contact(bot_session, contact, message_id, call_run_id)
        
        # Create tasks for all contacts
        tasks = [dial_with_semaphore(contact) for contact in contacts]
        
        # Execute all tasks
        await asyncio.gather(*tasks)
        
        logger.info(f"Bot {bot_id} completed dialing {len(contacts)} contacts")

async def _dial_single_contact(
    session: Session, 
    contact: Contact, 
    message_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None
) -> None:
    """
    Dials a single contact trying each phone number in priority order.
    
    Parameters:
    - session: The database session
    - contact: The contact to dial
    - message_id: Optional message ID to use for the call
    - call_run_id: Optional call run ID to associate with this call
    """
    try:
        # If we have a call_run_id, get the call run's custom_data
        call_run_custom_data = None
        if call_run_id:
            call_run = session.exec(select(CallRun).where(CallRun.id == call_run_id)).first()
            if call_run and call_run.custom_data:
                logger.info(f"Found custom_data in call run {call_run_id}: {call_run.custom_data}")
                call_run_custom_data = call_run.custom_data
            
        # Order numbers by priority
        numbers = sorted(contact.phone_numbers, key=lambda p: p.priority)
        # Skip contacts with no numbers
        if not numbers:
            return
        for idx, phone in enumerate(numbers):
            try:
                sid = _make_call(phone.number, message_id)
                log = CallLog(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    call_sid=sid,
                    started_at=datetime.utcnow(),
                    status="initiated",
                    answered=False,
                    message_id=message_id,
                    call_run_id=call_run_id,
                    custom_data=call_run_custom_data  # Copy custom_data from CallRun to CallLog
                )
                session.add(log)
                session.commit()
                
                # Update the call run with the new call if needed
                if call_run_id:
                    _update_call_run_stats(session, call_run_id)
                
                answered = await _wait_for_answer(session, sid)
                if answered:
                    # Update the call run stats
                    if call_run_id:
                        _update_call_run_stats(session, call_run_id)
                    return
                
                # Update log to no-answer
                log.status = "no-answer"
                session.add(log)
                session.commit()
                
                # Update the call run stats
                if call_run_id:
                    _update_call_run_stats(session, call_run_id)
                
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
                    call_run_id=call_run_id,
                    custom_data=call_run_custom_data  # Copy custom_data from CallRun to CallLog
                )
                session.add(log)
                session.commit()
                
                # Update the call run stats
                if call_run_id:
                    _update_call_run_stats(session, call_run_id)
                
                if idx < len(numbers) - 1:
                    await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
    except Exception as e:
        logger.error(f"Unexpected error dialing {contact.name}: {str(e)}", exc_info=True)
    
    # All attempts failed but only add a manual entry if
    # there are no existing entries or all existing entries have error status
    existing_logs = session.exec(
        select(CallLog)
        .where(CallLog.contact_id == contact.id)
        .where(CallLog.status.in_(["completed", "no-answer", "initiated"]))
    ).all()
    
    # Only create manual entry if there are no successful calls
    if not existing_logs:
        session.add(
            CallLog(
                contact_id=contact.id,
                phone_number_id=numbers[-1].id,
                call_sid=f"manual-{datetime.utcnow().isoformat()}",
                started_at=datetime.utcnow(),
                status="manual",
                answered=False,
                message_id=message_id,
                call_run_id=call_run_id,
                custom_data=call_run_custom_data  # Copy custom_data from CallRun to CallLog
            )
        )
        session.commit()
        
        # Update the call run stats
        if call_run_id:
            _update_call_run_stats(session, call_run_id)

def _make_call(to_number: str, message_id: Optional[uuid.UUID] = None) -> str:
    # Make sure we use the public Twilio callback URL
    base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
    url = f"{base_url}/voice"
    
    # Set up parameters for Twilio call - we'll pass message_id in the URL
    if message_id:
        url = f"{url}?message_id={message_id}"
    
    call = twilio_client.calls.create(
        to=to_number,
        from_=settings.TWILIO_FROM_NUMBER,
        url=url,
        timeout=settings.CALL_TIMEOUT_SEC,
        status_callback_event=["completed"],
        status_callback=f"{base_url}/call-status",
        status_callback_method="POST"
    )
    return call.sid

async def _wait_for_answer(session: Session, sid: str) -> bool:
    """
    Wait for a call to be answered, checking the call status periodically.
    
    Parameters:
    - session: Database session
    - sid: The Twilio call SID to check
    
    Returns:
    - True if the call was answered, False otherwise
    """
    logger.info(f"Waiting for answer on call with SID: {sid}")
    max_attempts = int(settings.CALL_TIMEOUT_SEC / 2) + 1
    
    for attempt in range(max_attempts):
        await asyncio.sleep(2)
        # Get the latest status from the database
        call: CallLog | None = session.exec(
            select(CallLog).where(CallLog.call_sid == sid)
        ).first()
        
        # Refresh the session to ensure we have the latest data
        session.refresh(call) if call else None
        
        if not call:
            logger.warning(f"Call with SID {sid} not found in database (attempt {attempt+1}/{max_attempts})")
            continue
            
        logger.debug(f"Check {attempt+1}/{max_attempts}: Call status={call.status}, answered={call.answered}, digits={call.digits}")
        
        # Check if the call has been answered based on DTMF digits or status
        if call.digits:
            # If we have DTMF input, the call was definitely answered
            call.status = "completed"
            call.answered = True
            session.add(call)
            session.commit()
            logger.info(f"Call {sid} marked as answered due to DTMF input: {call.digits}")
            return True
            
        elif call.answered:
            # If call is marked as answered for any reason
            logger.info(f"Call {sid} is already marked as answered")
            
            # Ensure status is also consistent
            if call.status != "completed":
                call.status = "completed"
                session.add(call)
                session.commit()
                logger.info(f"Updated status to 'completed' for answered call {sid}")
                
            return True
            
        elif call.status == "completed":
            # If status is completed, consider it answered
            call.answered = True
            session.add(call)
            session.commit()
            logger.info(f"Call {sid} marked as answered due to 'completed' status")
            return True
            
        # Check if we explicitly know the call was not answered
        elif call.status == "no-answer":
            logger.info(f"Call {sid} is explicitly marked as 'no-answer', stopping wait")
            return False
            
    logger.warning(f"Call {sid} wait timeout exceeded without answer")
    return False

def _update_call_run_stats(session: Session, call_run_id: uuid.UUID) -> None:
    """
    Update the statistics for a call run.
    
    Parameters:
    - session: The database session
    - call_run_id: The ID of the call run to update
    """
    try:
        # Get the call run
        call_run = session.exec(select(CallRun).where(CallRun.id == call_run_id)).first()
        if not call_run:
            logger.error(f"Call run with ID {call_run_id} not found when updating stats")
            return
        
        # Get updated counts
        total_calls = session.exec(
            select(CallLog).where(CallLog.call_run_id == call_run_id)
        ).count()
        completed_calls = session.exec(
            select(CallLog).where(
                (CallLog.call_run_id == call_run_id) & 
                (CallLog.status.in_(["completed", "no-answer", "manual", "error"]))
            )
        ).count()
        answered_calls = session.exec(
            select(CallLog).where(
                (CallLog.call_run_id == call_run_id) & 
                (CallLog.answered == True)
            )
        ).count()
        
        # Update the call run
        call_run.total_calls = total_calls
        call_run.completed_calls = completed_calls
        call_run.answered_calls = answered_calls
        
        # If all calls are completed, mark the call run as completed
        if completed_calls == total_calls and total_calls > 0:
            call_run.status = "completed"
            call_run.completed_at = datetime.now()
        
        session.add(call_run)
        session.commit()
    except Exception as e:
        logger.error(f"Error updating call run stats: {str(e)}", exc_info=True)

async def make_manual_call(
    contact_id: uuid.UUID,
    message_id: uuid.UUID,
    phone_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None
) -> None:
    """
    Make a manual call to a specific contact.
    
    Parameters:
    - contact_id: The ID of the contact to call
    - message_id: The ID of the message to use for the call
    - phone_id: Optional specific phone number ID to call. If not provided,
                will try all phone numbers in priority order.
    - call_run_id: Optional ID of a call run to associate this call with
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    
    call_logger = logging.getLogger("manual_call")
    call_logger.info(f"Starting manual call process for contact_id={contact_id}, message_id={message_id}, phone_id={phone_id}")
    
    with Session(engine) as session:
        # Load the contact
        try:
            contact = session.exec(
                select(Contact)
                .where(Contact.id == contact_id)
                .options(selectinload(Contact.phone_numbers))
            ).first()
            
            if not contact:
                call_logger.error(f"Contact with ID {contact_id} not found")
                return
            
            call_logger.info(f"Loaded contact: {contact.name} (ID: {contact.id})")
            
            # Load the message
            message = session.exec(
                select(Message)
                .where(Message.id == message_id)
            ).first()
            
            if not message:
                call_logger.error(f"Message with ID {message_id} not found")
                return
            
            call_logger.info(f"Loaded message: {message.name} (ID: {message.id})")
            
            # Determine which phone number(s) to call
            phones_to_try = []
            
            if phone_id:
                # Call only the specific phone number
                phone = session.exec(
                    select(PhoneNumber)
                    .where(
                        (PhoneNumber.id == phone_id) & 
                        (PhoneNumber.contact_id == contact_id)
                    )
                ).first()
                
                if phone:
                    phones_to_try = [phone]
                    call_logger.info(f"Using specified phone: {phone.number} (ID: {phone.id})")
                else:
                    call_logger.error(f"Phone number with ID {phone_id} not found for contact {contact.name}")
                    return
            else:
                # Sort phone numbers by priority
                phones_to_try = sorted(contact.phone_numbers, key=lambda p: p.priority)
                call_logger.info(f"Using all phones in priority order: {[p.number for p in phones_to_try]}")
            
            if not phones_to_try:
                call_logger.error(f"No phone numbers found for contact {contact.name}")
                return
            
            # Make the call(s)
            success = False
            
            for idx, phone in enumerate(phones_to_try):
                try:
                    call_logger.info(f"Attempt {idx+1}/{len(phones_to_try)}: Making manual call to {contact.name} at {phone.number}")
                    
                    # Create a call log entry
                    call_log = CallLog(
                        contact_id=contact.id,
                        phone_number_id=phone.id,
                        call_sid="pending",
                        started_at=datetime.now(),
                        answered=False,
                        status="manual",
                        message_id=message.id,
                        call_run_id=call_run_id
                    )
                    session.add(call_log)
                    session.commit()
                    call_logger.debug(f"Created call log entry ID: {call_log.id}")
                    
                    # Update call run stats if needed
                    if call_run_id:
                        _update_call_run_stats(session, call_run_id)
                    
                    # Make the call
                    call_sid = _make_call(phone.number, message_id)
                    call_logger.info(f"Call initiated with SID: {call_sid}")
                    
                    # Update the call log
                    call_log.call_sid = call_sid
                    session.add(call_log)
                    session.commit()
                    call_logger.debug(f"Updated call log with SID: {call_sid}")
                    
                    # Wait for call to be answered
                    answered = await _wait_for_answer(session, call_sid)
                    
                    if answered:
                        call_logger.info(f"Manual call to {contact.name} was answered")
                        success = True
                        
                        # Update call run stats if needed
                        if call_run_id:
                            _update_call_run_stats(session, call_run_id)
                        
                        break
                    else:
                        call_logger.warning(f"Manual call to {contact.name} was not answered")
                        
                        # Update the call log status
                        call_log.status = "no-answer"
                        session.add(call_log)
                        session.commit()
                        call_logger.debug(f"Updated call log status to no-answer")
                        
                        # Update call run stats if needed
                        if call_run_id:
                            _update_call_run_stats(session, call_run_id)
                    
                except Exception as e:
                    call_logger.error(f"Error making manual call to {contact.name}: {str(e)}", exc_info=True)
                    
                    # Update call log to show error
                    if 'call_log' in locals():
                        call_log.status = "error"
                        session.add(call_log)
                        session.commit()
                        call_logger.debug(f"Updated call log status to error")
                        
                        # Update call run stats if needed
                        if call_run_id:
                            _update_call_run_stats(session, call_run_id)
                        
                # If we have more numbers to try, wait before trying next number
                if idx < len(phones_to_try) - 1 and not success:
                    call_logger.info(f"Waiting {settings.SECONDARY_BACKOFF_SEC} seconds before trying next number")
            
            if not success:
                call_logger.warning(f"Manual call to {contact.name} failed on all phone numbers")
        except Exception as e:
            call_logger.error(f"Unexpected error in manual call process: {str(e)}", exc_info=True)
        
        # Removed duplicate warning log

async def make_custom_call(
    contact_id: uuid.UUID,
    message_content: str,
    phone_id: Optional[uuid.UUID] = None,
    dtmf_responses: Optional[List[dict]] = None,
    save_as_template: bool = False,
    template_name: Optional[str] = None,
    save_dtmf_responses: bool = False,
    call_run_id: Optional[uuid.UUID] = None
) -> None:
    """
    Make a custom call with specific message content and DTMF responses.
    
    Parameters:
    - contact_id: The ID of the contact to call
    - message_content: The message content to use for the call
    - phone_id: Optional specific phone number ID to call
    - dtmf_responses: Optional list of DTMF response configurations
    - save_as_template: Whether to save this message as a template
    - template_name: Name for the template if saving
    - save_dtmf_responses: Whether to save the DTMF responses as system defaults
    - call_run_id: Optional ID of a call run to associate this call with
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    from .models import CustomMessageLog, DtmfResponse
    
    with Session(engine) as session:
        # Load the contact
        contact = session.exec(
            select(Contact)
            .where(Contact.id == contact_id)
            .options(selectinload(Contact.phone_numbers))
        ).first()
        
        if not contact:
            logger.error(f"Contact with ID {contact_id} not found")
            return
        
        # First, create a message template if requested
        message_id = None
        if save_as_template and template_name:
            new_message = Message(
                name=template_name,
                content=message_content,
                is_template=True,
                message_type="voice",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            message_id = new_message.id
            logger.info(f"Created new message template: {template_name} with ID {message_id}")
        
        # Save DTMF responses if requested
        dtmf_config = {}
        if dtmf_responses:
            dtmf_config = {item.get('digit'): {
                'description': item.get('description', ''),
                'response_message': item.get('response_message', '')
            } for item in dtmf_responses}
            
            if save_dtmf_responses:
                # Save to system defaults
                for item in dtmf_responses:
                    digit = item.get('digit', '')
                    description = item.get('description', '')
                    response_message = item.get('response_message', '')
                    
                    if not digit or not response_message:
                        continue
                    
                    # Check if this digit already has a response
                    existing = session.exec(
                        select(DtmfResponse).where(DtmfResponse.digit == digit)
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.description = description
                        existing.response_message = response_message
                        existing.updated_at = datetime.now()
                        session.add(existing)
                    else:
                        # Create new
                        new_dtmf = DtmfResponse(
                            digit=digit,
                            description=description,
                            response_message=response_message,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        session.add(new_dtmf)
                
                session.commit()
                logger.info(f"Saved {len(dtmf_responses)} DTMF responses to system defaults")
        
        # Create a custom message log entry
        custom_message = CustomMessageLog(
            contact_id=contact_id,
            message_content=message_content,
            message_type="call",
            dtmf_responses=dtmf_config,
            created_at=datetime.now()
        )
        session.add(custom_message)
        session.commit()
        session.refresh(custom_message)
        
        # Determine which phone number(s) to call
        phones_to_try = []
        
        if phone_id:
            # Call only the specific phone number
            phone = session.exec(
                select(PhoneNumber)
                .where(
                    (PhoneNumber.id == phone_id) & 
                    (PhoneNumber.contact_id == contact_id)
                )
            ).first()
            
            if phone:
                phones_to_try = [phone]
            else:
                logger.error(f"Phone number with ID {phone_id} not found for contact {contact.name}")
                return
        else:
            # Sort phone numbers by priority
            phones_to_try = sorted(contact.phone_numbers, key=lambda p: p.priority)
        
        if not phones_to_try:
            logger.error(f"No phone numbers found for contact {contact.name}")
            return
        
        # Make the call(s)
        success = False
        
        for phone in phones_to_try:
            try:
                logger.info(f"Making custom call to {contact.name} at {phone.number}")
                
                # Create a call log entry
                call_log = CallLog(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    call_sid="pending",
                    started_at=datetime.now(),
                    answered=False,
                    status="custom",
                    message_id=message_id,
                    custom_message_log_id=custom_message.id,
                    call_run_id=call_run_id
                )
                session.add(call_log)
                session.commit()
                
                # Update call run stats if needed
                if call_run_id:
                    _update_call_run_stats(session, call_run_id)
                
                # Make the call with custom parameters
                base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
                url = f"{base_url}/custom-voice?custom_message_id={custom_message.id}"
                
                call = twilio_client.calls.create(
                    to=phone.number,
                    from_=settings.TWILIO_FROM_NUMBER,
                    url=url,
                    timeout=settings.CALL_TIMEOUT_SEC,
                    status_callback_event=["completed"],
                    status_callback=f"{base_url}/call-status",
                    status_callback_method="POST"
                )
                
                # Update the call log
                call_log.call_sid = call.sid
                session.add(call_log)
                session.commit()
                
                # Wait for call to be answered
                answered = await _wait_for_answer(session, call.sid)
                
                if answered:
                    logger.info(f"Custom call to {contact.name} was answered")
                    success = True
                    
                    # Update call run stats if needed
                    if call_run_id:
                        _update_call_run_stats(session, call_run_id)
                    
                    break
                else:
                    logger.warning(f"Custom call to {contact.name} was not answered")
                    
                    # Update the call log status
                    call_log.status = "no-answer"
                    session.add(call_log)
                    session.commit()
                    
                    # Update call run stats if needed
                    if call_run_id:
                        _update_call_run_stats(session, call_run_id)
                
            except Exception as e:
                logger.error(f"Error making custom call to {contact.name}: {e}")
                
                # Update call log to show error
                if 'call_log' in locals():
                    call_log.status = "error"
                    session.add(call_log)
                    session.commit()
                    
                    # Update call run stats if needed
                    if call_run_id:
                        _update_call_run_stats(session, call_run_id)
        
        if not success:
            logger.warning(f"Custom call to {contact.name} failed on all phone numbers")
            
    return
