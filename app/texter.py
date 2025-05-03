import re
import logging
import uuid
from datetime import datetime, timedelta
from typing import Sequence, Optional, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from .config import get_settings
from .models import Contact, PhoneNumber, SmsLog

settings = get_settings()
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

async def text_contacts(
    contacts: Sequence[uuid.UUID] | None = None,
    group_id: Optional[uuid.UUID] = None,
    message_id: Optional[uuid.UUID] = None,
) -> None:
    logging.debug(f"text_contacts called with: contacts={contacts}, group_id={group_id}, message_id={message_id}")
    """
    Background task entry point: load contacts in a fresh session and text each.
    
    Parameters:
    - contacts: If provided, only these specific contact IDs will be texted
    - group_id: If provided, only contacts in this group will be texted
    - message_id: Required - the message to send via SMS
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    from .models import GroupContactLink, Message
    
    if message_id is None:
        logging.error("No message_id provided for SMS")
        return
        
    with Session(engine) as session:
        # Verify message exists and is appropriate for SMS
        message = session.exec(select(Message).where(Message.id == message_id)).first()
        if not message:
            logging.error(f"Message with ID {message_id} not found")
            return
            
        if message.message_type not in ["sms", "both"]:
            logging.error(f"Message with ID {message_id} is not configured for SMS (type: {message.message_type})")
            return
        
        # Load contacts (with phone numbers) in this session
        if contacts is not None:
            # Specific contacts requested
            logging.debug(f"Fetching {len(contacts) if contacts else 0} specific contacts by ID")
            results = session.exec(
                select(Contact)
                .where(Contact.id.in_(contacts))
                .options(selectinload(Contact.phone_numbers))
            )
            to_text = results.all()
            logging.debug(f"Found {len(to_text)} contacts out of {len(contacts) if contacts else 0} requested IDs")
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
                to_text = results.all()
            else:
                to_text = []
        else:
            # All contacts
            results = session.exec(
                select(Contact).options(selectinload(Contact.phone_numbers))
            )
            to_text = results.all()
            
        # Text each contact
        logging.debug(f"Preparing to text {len(to_text)} contacts")
        for i, contact in enumerate(to_text):
            logging.debug(f"Processing contact {i+1}/{len(to_text)}: {contact.name} (ID: {contact.id})")
            await _text_single_contact(session, contact, message_id)
            
        logging.info(f"SMS sending completed for {len(to_text)} contacts")

async def _text_single_contact(
    session: Session, 
    contact: Contact, 
    message_id: uuid.UUID,
    retry_count: int = 0,
    retry_delay_minutes: int = 30,
    custom_message_log_id: Optional[uuid.UUID] = None,
    scheduled_message_id: Optional[uuid.UUID] = None
) -> None:
    logging.debug(f"_text_single_contact: Processing contact {contact.name} (ID: {contact.id})")
    logging.debug(f"Parameters: message_id={message_id}, retry_count={retry_count}, custom_msg_id={custom_message_log_id}, scheduled_id={scheduled_message_id}")
    """
    Send an SMS to a single contact using their primary number.
    
    Parameters:
    - session: Database session
    - contact: Contact object to text
    - message_id: ID of the message to send
    - retry_count: How many times to retry if sending fails
    - retry_delay_minutes: How many minutes to wait between retries
    - custom_message_log_id: Optional ID of a custom message log entry
    - scheduled_message_id: Optional ID of a scheduled message
    """
    from .models import Message
    
    try:
        # Load the message content
        message = session.exec(select(Message).where(Message.id == message_id)).first()
        if not message:
            logging.error(f"Message with ID {message_id} not found")
            return
        
        # Get message content
        message_content = message.content
        if not message_content or message_content.strip() == "":
            logging.error(f"Message with ID {message_id} has no content")
            return
        logging.debug(f"Message content length: {len(message_content)} characters")
            
        # Respect SMS length limits (160 chars)
        # message_content = message_content[:160]
        
        # Order phone numbers by priority
        numbers = sorted(contact.phone_numbers, key=lambda p: p.priority)
        
        # Skip contacts with no numbers
        if not numbers:
            logging.warning(f"Contact {contact.name} has no phone numbers, skipping SMS")
            return
        
        logging.debug(f"Found {len(numbers)} phone numbers for contact {contact.name}")
        for i, phone in enumerate(numbers):
            logging.debug(f"  Phone {i+1}: {phone.number} (priority: {phone.priority}, type: {phone.number_type if hasattr(phone, 'number_type') else 'unknown'})")
        
        for phone in numbers:
            try:
                logging.debug(f"Attempting to send SMS to {contact.name} at phone: {phone.number}")
                # Send the SMS
                sid = _send_sms(phone.number, message_content)
                
                # Log the success
                log = SmsLog(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    message_sid=sid,
                    sent_at=datetime.utcnow(),
                    status="sent",
                    message_id=message_id,
                    retry_count=0,
                    is_retry=False,
                    custom_message_log_id=custom_message_log_id,
                    scheduled_message_id=scheduled_message_id
                )
                session.add(log)
                session.commit()
                logging.info(f"SMS sent to {contact.name} at {phone.number}")
                
                # One successful number is enough, so break the loop
                break
                
            except TwilioRestException as e:
                # Log the error
                retry_at = None
                if retry_count > 0:
                    retry_at = datetime.utcnow() + timedelta(minutes=retry_delay_minutes)
                    
                log = SmsLog(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    message_sid=f"error-{datetime.utcnow().isoformat()}",
                    sent_at=datetime.utcnow(),
                    status="failed",
                    message_id=message_id,
                    retry_count=retry_count,
                    retry_at=retry_at,
                    is_retry=False,
                    custom_message_log_id=custom_message_log_id,
                    scheduled_message_id=scheduled_message_id
                )
                session.add(log)
                session.commit()
                logging.error(f"Failed to send SMS to {contact.name} at {phone.number}: {str(e)}")
                
                # Continue to next number if available
    except Exception as e:
        logging.error(f"Unexpected error sending SMS to {contact.name}: {str(e)}", exc_info=True)

async def send_custom_sms(
    message_id: Optional[uuid.UUID] = None,
    contact_list: Optional[List[uuid.UUID]] = None,
    group_id: Optional[uuid.UUID] = None,
    message_content: Optional[str] = None,
    save_as_template: bool = False,
    template_name: Optional[str] = None,
    schedule_time: Optional[datetime] = None,
    retry_count: int = 0,
    retry_delay_minutes: int = 30
) -> None:
    """
    Send a custom SMS message to recipients or group
    
    Parameters:
    - message_id: Optional ID of a message to use as template
    - contact_list: List of contact IDs to send SMS to
    - group_id: Optional group ID to send to
    - message_content: Custom SMS message content (only used if message_id is None)
    - save_as_template: Whether to save this message as a template
    - template_name: Name for the template if saving
    - schedule_time: Optional future time to schedule the message
    - retry_count: Number of retries for failed SMS
    - retry_delay_minutes: Delay between retries in minutes
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    from .models import GroupContactLink, Message, CustomMessageLog, ScheduledMessage, ScheduledMessageContactLink
    
    with Session(engine) as session:
        # If scheduling for future, create a scheduled message
        if schedule_time and schedule_time > datetime.now():
            # Create message if template requested or message_id not provided
            if message_id is None and message_content:
                if save_as_template and template_name:
                    new_message = Message(
                        name=template_name,
                        content=message_content,
                        is_template=True,
                        message_type="sms",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(new_message)
                    session.commit()
                    session.refresh(new_message)
                    message_id = new_message.id
                    logging.info(f"Created new SMS template: {template_name} with ID {message_id}")
            
            # Create a scheduled message
            scheduled_message = ScheduledMessage(
                name=template_name or f"Scheduled SMS for {schedule_time.strftime('%Y-%m-%d %H:%M')}",
                message_id=message_id if message_id else None,
                group_id=group_id,
                message_type="sms",
                schedule_time=schedule_time,
                recurring=False,
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(scheduled_message)
            session.commit()
            session.refresh(scheduled_message)
            
            # If we have specific recipients, link them
            if contact_list:
                for contact_id in contact_list:
                    link = ScheduledMessageContactLink(
                        scheduled_message_id=scheduled_message.id,
                        contact_id=contact_id
                    )
                    session.add(link)
                    
            session.commit()
            logging.info(f"Scheduled SMS for delivery at {schedule_time}")
            return
        
        # For immediate sending, either use existing message or create a new one
        if message_id:
            # Use existing message
            message = session.exec(select(Message).where(Message.id == message_id)).first()
            if not message:
                logging.error(f"Message with ID {message_id} not found")
                return
            
            message_content = message.content
        elif not message_content:
            logging.error("Either message_id or message_content must be provided")
            return
        
        # Create message template if requested
        if message_id is None and save_as_template and template_name:
            new_message = Message(
                name=template_name,
                content=message_content,
                is_template=True,
                message_type="sms",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            message_id = new_message.id
            logging.info(f"Created new SMS template: {template_name} with ID {message_id}")
        
        # Create custom message log if using custom content
        custom_message_id = None
        if message_id is None:
            # Using custom content, log it
            custom_message = CustomMessageLog(
                contact_id=contact_list[0] if contact_list and len(contact_list) > 0 else None,
                message_content=message_content,
                message_type="sms",
                created_at=datetime.now()
            )
            session.add(custom_message)
            session.commit()
            session.refresh(custom_message)
            custom_message_id = custom_message.id
        
        # Load contacts
        contacts_to_text = []
        
        if contact_list:
            results = session.exec(
                select(Contact)
                .where(Contact.id.in_(contact_list))
                .options(selectinload(Contact.phone_numbers))
            )
            contacts_to_text = results.all()
            
        elif group_id:
            # Get contacts in this group
            contact_links = session.exec(
                select(GroupContactLink).where(GroupContactLink.group_id == group_id)
            ).all()
            
            if contact_links:
                contact_ids = [link.contact_id for link in contact_links]
                results = session.exec(
                    select(Contact)
                    .where(Contact.id.in_(contact_ids))
                    .options(selectinload(Contact.phone_numbers))
                )
                contacts_to_text = results.all()
        
        # Send to each contact
        for contact in contacts_to_text:
            if message_id:
                # If using template, use that
                await _text_single_contact(
                    session=session,
                    contact=contact,
                    message_id=message_id,
                    retry_count=retry_count,
                    retry_delay_minutes=retry_delay_minutes,
                    custom_message_log_id=custom_message_id
                )
            else:
                # No template, use the content directly
                # Order numbers by priority
                numbers = sorted(contact.phone_numbers, key=lambda p: p.priority)
                
                if not numbers:
                    logging.warning(f"Contact {contact.name} has no phone numbers, skipping SMS")
                    continue
                    
                # Try each number
                for phone in numbers:
                    try:
                        sid = _send_sms(phone.number, message_content)
                        
                        # Log the SMS
                        log = SmsLog(
                            contact_id=contact.id,
                            phone_number_id=phone.id,
                            message_sid=sid,
                            sent_at=datetime.utcnow(),
                            status="sent",
                            message_id=None,
                            retry_count=0,
                            is_retry=False,
                            custom_message_log_id=custom_message_id
                        )
                        session.add(log)
                        session.commit()
                        logging.info(f"Custom SMS sent to {contact.name} at {phone.number}")
                        
                        # One number is enough
                        break
                            
                    except TwilioRestException as e:
                        # Log the error
                        retry_at = None
                        if retry_count > 0:
                            retry_at = datetime.utcnow() + timedelta(minutes=retry_delay_minutes)
                            
                        log = SmsLog(
                            contact_id=contact.id,
                            phone_number_id=phone.id,
                            message_sid=f"error-{datetime.utcnow().isoformat()}",
                            sent_at=datetime.utcnow(),
                            status="failed",
                            message_id=None,
                            retry_count=retry_count,
                            retry_at=retry_at,
                            is_retry=False,
                            custom_message_log_id=custom_message_id
                        )
                        session.add(log)
                        session.commit()
                        logging.error(f"Failed to send custom SMS to {contact.name} at {phone.number}: {str(e)}")
        
        logging.info(f"Custom SMS sending completed for {len(contacts_to_text)} contacts")

def _send_sms(to_number: str, message_content: str) -> str:
    """Send SMS using Twilio API and return the message SID"""
    logging.debug(f"Preparing to send SMS to {to_number} with content length: {len(message_content)}")
    logging.debug(f"Using Twilio account: {settings.TWILIO_ACCOUNT_SID[:4]}...{settings.TWILIO_ACCOUNT_SID[-4:]}")
    logging.debug(f"Using from number: {settings.TWILIO_FROM_NUMBER}")
    message = twilio_client.messages.create(
        to=to_number,
        from_=settings.TWILIO_FROM_NUMBER,
        body=message_content
    )
    logging.debug(f"Successfully sent SMS, received message SID: {message.sid}")
    return message.sid