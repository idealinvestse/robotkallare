"""SMS service for sending SMS messages."""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Union

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlmodel import Session

from app.config import get_settings
from app.models import Contact, Message
from app.repositories.sms_repository import SmsRepository

logger = logging.getLogger(__name__)
settings = get_settings()

class SmsService:
    """Service for SMS-related operations."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.repository = SmsRepository(session)
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    def send_sms(self, to_number: str, message_content: str) -> str:
        """Send an SMS using Twilio API and return the message SID."""
        logger.debug(f"Preparing to send SMS to {to_number} with content length: {len(message_content)}")
        logger.debug(f"Using Twilio account: {settings.TWILIO_ACCOUNT_SID[:4]}...{settings.TWILIO_ACCOUNT_SID[-4:]}")
        logger.debug(f"Using from number: {settings.TWILIO_FROM_NUMBER}")
        message = self.twilio_client.messages.create(
            to=to_number,
            from_=settings.TWILIO_FROM_NUMBER,
            body=message_content
        )
        logger.debug(f"Successfully sent SMS, received message SID: {message.sid}")
        return message.sid
    
    async def send_message_to_contacts(
        self,
        message_id: Union[uuid.UUID, str],
        contact_ids: Optional[Sequence[uuid.UUID]] = None,
        group_id: Optional[uuid.UUID] = None,
        retry_count: int = 0,
        retry_delay_minutes: int = 30
    ) -> Dict[str, Union[int, List[str]]]:
        logger.debug(f"Starting send_message_to_contacts with message_id: {message_id}")
        logger.debug(f"Parameters - contact_ids: {contact_ids}, group_id: {group_id}, retry_count: {retry_count}, retry_delay_minutes: {retry_delay_minutes}")
        """
        Send an SMS message to contacts or a group.
        
        Args:
            message_id: The message template ID
            contact_ids: Optional list of specific contact IDs
            group_id: Optional group ID to send to everyone in the group
            retry_count: Number of retries if sending fails
            retry_delay_minutes: Minutes between retries
            
        Returns:
            A dictionary with success stats and any errors
        """
        result = {
            "sent_count": 0,
            "failed_count": 0,
            "errors": []
        }
        
        # Get the message
        logger.debug(f"Fetching message with ID: {message_id}")
        message = self.repository.get_message_by_id(message_id)
        if not message:
            error = f"Message with ID {message_id} not found"
            logger.error(error)
            result["errors"].append(error)
            logger.debug(f"Returning early with error: {error}")
            return result
        logger.debug(f"Found message: {message.name} (type: {message.message_type})")
            
        # Verify message is for SMS
        if message.message_type not in ["sms", "both"]:
            error = f"Message '{message.name}' is not configured for SMS (type: {message.message_type})"
            logger.error(error)
            result["errors"].append(error)
            return result
        
        # Get contacts
        contacts = []
        if contact_ids:
            logger.debug(f"Fetching {len(contact_ids) if contact_ids else 0} specific contacts by IDs")
            contacts = self.repository.get_contacts_by_ids(contact_ids)
        elif group_id:
            logger.debug(f"Fetching contacts for group ID: {group_id}")
            contacts = self.repository.get_contacts_by_group_id(group_id)
        else:
            logger.debug(f"Fetching all contacts")
            contacts = self.repository.get_all_contacts()
        logger.debug(f"Retrieved {len(contacts)} contacts to message")
            
        # Send to each contact
        contact_count = 0
        for contact in contacts:
            contact_count += 1
            logger.debug(f"Processing contact {contact_count}/{len(contacts)}: {contact.name} (ID: {contact.id})")
            success = await self._send_to_contact(
                contact=contact,
                message=message,
                retry_count=retry_count,
                retry_delay_minutes=retry_delay_minutes
            )
            
            if success:
                result["sent_count"] += 1
                logger.debug(f"Successfully sent to contact {contact.name}")
            else:
                result["failed_count"] += 1
                logger.debug(f"Failed to send to contact {contact.name}")
                
        logger.info(f"SMS sending completed: {result['sent_count']} sent, {result['failed_count']} failed")
        return result
        
    async def _send_to_contact(
        self,
        contact: Contact,
        message: Message,
        retry_count: int = 0,
        retry_delay_minutes: int = 30,
        custom_message_log_id: Optional[uuid.UUID] = None,
        scheduled_message_id: Optional[uuid.UUID] = None
    ) -> bool:
        logger.debug(f"_send_to_contact: Processing contact {contact.name} (ID: {contact.id})")
        logger.debug(f"Message: {message.name}, retry_count: {retry_count}, custom_msg_id: {custom_message_log_id}, scheduled_id: {scheduled_message_id}")
        """
        Send an SMS to a single contact.
        
        Args:
            contact: The contact object with phone numbers
            message: The message object with content
            retry_count: Number of retries if sending fails
            retry_delay_minutes: Minutes between retries
            custom_message_log_id: Optional custom message log ID
            scheduled_message_id: Optional scheduled message ID
            
        Returns:
            True if sent successfully to at least one number, False otherwise
        """
        try:
            message_content = message.content
            if not message_content or message_content.strip() == "":
                logger.error(f"Message '{message.name}' has no content")
                return False
                
            # Get phone numbers
            logger.debug(f"Retrieving phone numbers for contact {contact.name}")
            phones, errors = self.repository.get_phone_for_contact(contact)
            if not phones:
                for error in errors:
                    logger.warning(error)
                logger.debug(f"No valid phone numbers found for contact {contact.name}")
                return False
            logger.debug(f"Found {len(phones)} phone numbers for contact {contact.name}")
                
            # Try each phone number in priority order
            for phone in phones:
                try:
                    logger.debug(f"Attempting to send SMS to {contact.name} at phone: {phone.number} (priority: {phone.priority})")
                    # Send SMS
                    sid = self.send_sms(phone.number, message_content)
                    
                    # Log success
                    self.repository.create_sms_log(
                        contact_id=contact.id,
                        phone_number_id=phone.id,
                        message_sid=sid,
                        status="sent",
                        message_id=message.id,
                        retry_count=0,
                        is_retry=False,
                        custom_message_log_id=custom_message_log_id,
                        scheduled_message_id=scheduled_message_id
                    )
                    
                    logger.info(f"SMS sent to {contact.name} at {phone.number}")
                    return True  # Success, no need to try other numbers
                    
                except TwilioRestException as e:
                    # Log failure
                    retry_at = None
                    if retry_count > 0:
                        retry_at = datetime.utcnow() + timedelta(minutes=retry_delay_minutes)
                        
                    self.repository.create_sms_log(
                        contact_id=contact.id,
                        phone_number_id=phone.id,
                        message_sid=f"error-{datetime.utcnow().isoformat()}",
                        status="failed",
                        message_id=message.id,
                        retry_count=retry_count,
                        retry_at=retry_at,
                        is_retry=False,
                        custom_message_log_id=custom_message_log_id,
                        scheduled_message_id=scheduled_message_id
                    )
                    
                    logger.error(f"Failed to send SMS to {contact.name} at {phone.number}: {str(e)}")
                    # Continue to next number
                    
            # All numbers failed
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {contact.name}: {str(e)}", exc_info=True)
            return False
            
    async def send_custom_sms(
        self,
        message_content: Optional[str] = None,
        message_id: Optional[uuid.UUID] = None,
        contact_list: Optional[List[uuid.UUID]] = None,
        group_id: Optional[uuid.UUID] = None,
        save_as_template: bool = False,
        template_name: Optional[str] = None,
        schedule_time: Optional[datetime] = None,
        retry_count: int = 0,
        retry_delay_minutes: int = 30
    ) -> Dict[str, Union[int, str, List[str]]]:
        """
        Send a custom SMS or schedule it for later.
        
        Args:
            message_content: Custom message content (required if message_id not provided)
            message_id: Existing message template ID (required if message_content not provided)
            contact_list: List of contact IDs to send to
            group_id: Group ID to send to
            save_as_template: Whether to save as template
            template_name: Name for the template if saving
            schedule_time: When to schedule the message
            retry_count: Retry count for failed messages
            retry_delay_minutes: Minutes between retries
            
        Returns:
            A dictionary with results and any errors
        """
        result = {
            "status": "error",
            "sent_count": 0,
            "failed_count": 0,
            "errors": []
        }
        
        # Validate inputs
        if not message_id and not message_content:
            error = "Either message_id or message_content must be provided"
            logger.error(error)
            result["errors"].append(error)
            return result
            
        if not contact_list and not group_id:
            error = "Either contact_list or group_id must be provided"
            logger.error(error)
            result["errors"].append(error)
            return result
            
        # Handle scheduling for future
        if schedule_time and schedule_time > datetime.now():
            try:
                # Create message template if needed
                template_id = message_id
                if not template_id and save_as_template and template_name and message_content:
                    template = self.repository.create_template_message(
                        name=template_name,
                        content=message_content,
                        message_type="sms"
                    )
                    template_id = template.id
                    logger.info(f"Created new SMS template: {template_name} with ID {template_id}")
                
                # Create scheduled message
                name = template_name or f"Scheduled SMS for {schedule_time.strftime('%Y-%m-%d %H:%M')}"
                scheduled = self.repository.create_scheduled_message(
                    name=name,
                    schedule_time=schedule_time,
                    message_type="sms",
                    message_id=template_id,
                    group_id=group_id
                )
                
                # Add contacts if provided
                if contact_list:
                    self.repository.add_contacts_to_scheduled_message(
                        scheduled_message_id=scheduled.id,
                        contact_ids=contact_list
                    )
                    
                logger.info(f"Scheduled SMS for delivery at {schedule_time}")
                
                result["status"] = "scheduled"
                result["scheduled_id"] = str(scheduled.id)
                result["scheduled_time"] = schedule_time.isoformat()
                return result
                
            except Exception as e:
                error = f"Failed to schedule SMS: {str(e)}"
                logger.error(error, exc_info=True)
                result["errors"].append(error)
                return result
        
        # Send immediately
        try:
            # If using existing message
            if message_id:
                message = self.repository.get_message_by_id(message_id)
                if not message:
                    error = f"Message with ID {message_id} not found"
                    logger.error(error)
                    result["errors"].append(error)
                    return result
                    
                # Use template message
                return await self.send_message_to_contacts(
                    message_id=message_id,
                    contact_ids=contact_list,
                    group_id=group_id,
                    retry_count=retry_count,
                    retry_delay_minutes=retry_delay_minutes
                )
                
            # Using custom message content
            # Get the first contact ID for the log, if available
            first_contact_id = None
            if contact_list and len(contact_list) > 0:
                first_contact_id = contact_list[0]
                logger.debug(f"Using first contact ID for custom message log: {first_contact_id}")
                
            custom_log = self.repository.create_custom_message_log(
                message_content=message_content,
                contact_id=first_contact_id
            )
            
            # Create template if requested
            if save_as_template and template_name:
                template = self.repository.create_template_message(
                    name=template_name,
                    content=message_content,
                    message_type="sms"
                )
                logger.info(f"Created new SMS template: {template_name} with ID {template.id}")
                
                # Now use the template
                return await self.send_message_to_contacts(
                    message_id=template.id,
                    contact_ids=contact_list,
                    group_id=group_id,
                    retry_count=retry_count,
                    retry_delay_minutes=retry_delay_minutes
                )
            
            # Get contacts
            contacts = []
            if contact_list:
                contacts = self.repository.get_contacts_by_ids(contact_list)
            elif group_id:
                contacts = self.repository.get_contacts_by_group_id(group_id)
                
            # Create temporary message object for _send_to_contact
            temp_message = Message(
                id=None,
                name="Custom SMS",
                content=message_content,
                is_template=False,
                message_type="sms"
            )
            
            # Send to each contact
            for contact in contacts:
                success = await self._send_to_contact(
                    contact=contact,
                    message=temp_message,
                    retry_count=retry_count,
                    retry_delay_minutes=retry_delay_minutes,
                    custom_message_log_id=custom_log.id
                )
                
                if success:
                    result["sent_count"] += 1
                else:
                    result["failed_count"] += 1
                    
            result["status"] = "sent"
            logger.info(f"Custom SMS sending completed: {result['sent_count']} sent, {result['failed_count']} failed")
            return result
            
        except Exception as e:
            error = f"Failed to send custom SMS: {str(e)}"
            logger.error(error, exc_info=True)
            result["errors"].append(error)
            return result