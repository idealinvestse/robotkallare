"""Call service for making phone calls."""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Union

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlmodel import Session

from app.config import get_settings
from app.models import Contact, Message
from app.repositories.call_repository import CallRepository

logger = logging.getLogger(__name__)
settings = get_settings()

class CallService:
    """Service for call-related operations."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.repository = CallRepository(session)
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    def make_twilio_call(
        self, 
        to_number: str, 
        message_id: Optional[uuid.UUID] = None,
        custom_message_id: Optional[uuid.UUID] = None
    ) -> str:
        """Make a call using Twilio API and return the call SID."""
        # Set up callback URLs
        base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Determine which URL to use based on what parameters we received
        if custom_message_id:
            url = f"{base_url}/custom-voice?custom_message_id={custom_message_id}"
        else:
            url = f"{base_url}/voice"
            if message_id:
                url = f"{url}?message_id={message_id}"
                
        # Create the call
        call = self.twilio_client.calls.create(
            to=to_number,
            from_=settings.TWILIO_FROM_NUMBER,
            url=url,
            timeout=settings.CALL_TIMEOUT_SEC,
            status_callback_event=["completed"],
            status_callback=f"{base_url}/call-status",
            status_callback_method="POST"
        )
        return call.sid
    
    async def dial_contacts(
        self,
        contacts: Optional[Sequence[uuid.UUID]] = None,
        group_id: Optional[uuid.UUID] = None,
        message_id: Optional[uuid.UUID] = None,
        call_run_name: Optional[str] = None,
        call_run_description: Optional[str] = None,
        existing_call_run_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Union[str, int, List[str]]]:
        """
        Dial contacts or a group with a message.
        
        Args:
            contacts: Specific contact IDs to call
            group_id: Group ID to call all members
            message_id: Message ID to use for calls
            call_run_name: Name for a new call run
            call_run_description: Description for a new call run
            existing_call_run_id: ID of an existing call run
            
        Returns:
            Dictionary with results and any errors
        """
        result = {
            "status": "success",
            "total_contacts": 0,
            "completed_calls": 0,
            "answered_calls": 0,
            "errors": []
        }
        
        # Get the contacts to dial
        contact_objects = []
        if contacts:
            contact_objects = self.repository.get_contacts_by_ids(contacts)
        elif group_id:
            contact_objects = self.repository.get_contacts_by_group_id(group_id)
        else:
            contact_objects = self.repository.get_all_contacts()
            
        if not contact_objects:
            error = "No contacts found to dial"
            logger.error(error)
            result["errors"].append(error)
            result["status"] = "error"
            return result
            
        result["total_contacts"] = len(contact_objects)
        
        # Get or create a call run
        call_run = None
        if existing_call_run_id:
            call_run = self.repository.get_call_run(existing_call_run_id)
            if not call_run:
                error = f"Call run with ID {existing_call_run_id} not found"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
        elif call_run_name:
            # Create a new call run
            call_run = self.repository.create_call_run(
                name=call_run_name,
                description=call_run_description,
                message_id=message_id,
                group_id=group_id,
                total_calls=len(contact_objects)
            )
            logger.info(f"Created new call run: {call_run.name} (ID: {call_run.id})")
            result["call_run_id"] = str(call_run.id)
        
        # Dial each contact
        for contact in contact_objects:
            try:
                await self._dial_single_contact(
                    contact=contact,
                    message_id=message_id,
                    call_run_id=call_run.id if call_run else None
                )
            except Exception as e:
                error = f"Error dialing {contact.name}: {str(e)}"
                logger.error(error, exc_info=True)
                result["errors"].append(error)
        
        # Update call run stats if we have one
        if call_run:
            updated_run = self.repository.update_call_run_stats(call_run.id)
            if updated_run:
                result["completed_calls"] = updated_run.completed_calls
                result["answered_calls"] = updated_run.answered_calls
                result["call_run_status"] = updated_run.status
        
        return result
    
    async def _dial_single_contact(
        self,
        contact: Contact,
        message_id: Optional[uuid.UUID] = None,
        call_run_id: Optional[uuid.UUID] = None,
        custom_message_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Dial a single contact, trying each number in priority order.
        
        Args:
            contact: Contact object to dial
            message_id: Message ID to use
            call_run_id: Call run ID to associate with
            custom_message_id: Custom message ID to use
            
        Returns:
            True if answered, False otherwise
        """
        phones, errors = self.repository.get_phone_for_contact(contact)
        if not phones:
            for error in errors:
                logger.warning(error)
            return False
        
        for idx, phone in enumerate(phones):
            try:
                # Make the call
                call_sid = self.make_twilio_call(
                    to_number=phone.number,
                    message_id=message_id,
                    custom_message_id=custom_message_id
                )
                
                # Log the call
                call_log = self.repository.create_call_log(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    call_sid=call_sid,
                    status="initiated",
                    message_id=message_id,
                    custom_message_log_id=custom_message_id,
                    call_run_id=call_run_id
                )
                
                # Update call run stats if needed
                if call_run_id:
                    self.repository.update_call_run_stats(call_run_id)
                
                # Wait for answer
                answered = await self._wait_for_answer(call_sid)
                if answered:
                    # Update the call run stats if needed
                    if call_run_id:
                        self.repository.update_call_run_stats(call_run_id)
                    return True
                
                # Update log to no-answer
                call_log.status = "no-answer"
                self.repository.update_call_log(call_log)
                
                # Update call run stats if needed
                if call_run_id:
                    self.repository.update_call_run_stats(call_run_id)
                
                # Try next number after a delay if this one failed
                if idx < len(phones) - 1:
                    await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
                    
            except TwilioRestException as e:
                # Log error
                self.repository.create_call_log(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    call_sid=f"error-{datetime.utcnow().isoformat()}",
                    status="error",
                    message_id=message_id,
                    custom_message_log_id=custom_message_id,
                    call_run_id=call_run_id
                )
                
                # Update call run stats if needed
                if call_run_id:
                    self.repository.update_call_run_stats(call_run_id)
                
                logger.error(f"Twilio error calling {contact.name} at {phone.number}: {str(e)}")
                
                # Try next number after a delay
                if idx < len(phones) - 1:
                    await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
        
        # If we've reached here, all attempts failed
        # Check for existing successful calls first
        existing_logs = self.session.exec(
            select(CallLog)
            .where(CallLog.contact_id == contact.id)
            .where(CallLog.status.in_(["completed", "no-answer", "initiated"]))
        ).all()
        
        # Only create manual entry if there are no successful calls
        if not existing_logs:
            self.repository.create_call_log(
                contact_id=contact.id,
                phone_number_id=phones[-1].id,  # Use last attempted number
                call_sid=f"manual-{datetime.utcnow().isoformat()}",
                status="manual",
                message_id=message_id,
                custom_message_log_id=custom_message_id,
                call_run_id=call_run_id
            )
            
            # Update call run stats if needed
            if call_run_id:
                self.repository.update_call_run_stats(call_run_id)
        
        return False
    
    async def _wait_for_answer(self, call_sid: str) -> bool:
        """
        Wait for a call to be answered.
        
        Args:
            call_sid: Twilio call SID to watch
            
        Returns:
            True if call was answered, False otherwise
        """
        max_attempts = int(settings.CALL_TIMEOUT_SEC / 2) + 1
        for _ in range(max_attempts):
            await asyncio.sleep(2)
            call_log = self.repository.get_call_log_by_sid(call_sid)
            if call_log and call_log.answered:
                return True
        return False
    
    async def make_manual_call(
        self,
        contact_id: uuid.UUID,
        message_id: uuid.UUID,
        phone_id: Optional[uuid.UUID] = None,
        call_run_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Union[str, bool, List[str]]]:
        """
        Make a manual call to a specific contact.
        
        Args:
            contact_id: Contact ID to call
            message_id: Message ID to use
            phone_id: Specific phone ID to use (optional)
            call_run_id: Call run ID to associate with (optional)
            
        Returns:
            Dictionary with results
        """
        result = {
            "success": False,
            "contact_id": str(contact_id),
            "message_id": str(message_id),
            "errors": []
        }
        
        contact_objects = self.repository.get_contacts_by_ids([contact_id])
        if not contact_objects:
            error = f"Contact with ID {contact_id} not found"
            logger.error(error)
            result["errors"].append(error)
            return result
        
        contact = contact_objects[0]
        
        # Check message exists
        message = self.repository.get_message_by_id(message_id)
        if not message:
            error = f"Message with ID {message_id} not found"
            logger.error(error)
            result["errors"].append(error)
            return result
            
        # Determine which phone numbers to use
        phones_to_try = []
        if phone_id:
            # Look for specific number
            for phone in contact.phone_numbers:
                if phone.id == phone_id:
                    phones_to_try = [phone]
                    break
                    
            if not phones_to_try:
                error = f"Phone number with ID {phone_id} not found for contact {contact.name}"
                logger.error(error)
                result["errors"].append(error)
                return result
        else:
            # Use all numbers in priority order
            phones_to_try = sorted(contact.phone_numbers, key=lambda p: p.priority)
            
        if not phones_to_try:
            error = f"No phone numbers found for contact {contact.name}"
            logger.error(error)
            result["errors"].append(error)
            return result
            
        # Create a call log entry first
        call_log = self.repository.create_call_log(
            contact_id=contact.id,
            phone_number_id=phones_to_try[0].id,
            call_sid="pending",
            status="manual",
            message_id=message.id,
            call_run_id=call_run_id
        )
        
        # Update call run stats if needed
        if call_run_id:
            self.repository.update_call_run_stats(call_run_id)
            
        # Attempt the call
        for idx, phone in enumerate(phones_to_try):
            try:
                logger.info(f"Making manual call to {contact.name} at {phone.number}")
                
                # Make the call
                call_sid = self.make_twilio_call(
                    to_number=phone.number,
                    message_id=message_id
                )
                
                # Update the call log
                call_log.call_sid = call_sid
                self.repository.update_call_log(call_log)
                
                # Wait for answer
                answered = await self._wait_for_answer(call_sid)
                
                if answered:
                    logger.info(f"Manual call to {contact.name} was answered")
                    result["success"] = True
                    
                    # Update call run stats if needed
                    if call_run_id:
                        self.repository.update_call_run_stats(call_run_id)
                        
                    return result
                else:
                    logger.warning(f"Manual call to {contact.name} was not answered")
                    
                    # Update log status
                    call_log.status = "no-answer"
                    self.repository.update_call_log(call_log)
                    
                    # Update call run stats if needed
                    if call_run_id:
                        self.repository.update_call_run_stats(call_run_id)
                        
                    # Try next number if available
                    if idx < len(phones_to_try) - 1:
                        await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
                        
            except Exception as e:
                error = f"Error making call to {contact.name} at {phone.number}: {str(e)}"
                logger.error(error, exc_info=True)
                result["errors"].append(error)
                
                # Update log status
                call_log.status = "error"
                self.repository.update_call_log(call_log)
                
                # Update call run stats if needed
                if call_run_id:
                    self.repository.update_call_run_stats(call_run_id)
                    
                # Try next number if available
                if idx < len(phones_to_try) - 1:
                    await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
                    
        # All attempts failed
        result["success"] = False
        if not result["errors"]:
            result["errors"].append(f"Failed to call {contact.name} on all numbers")
            
        return result
    
    async def make_custom_call(
        self,
        contact_id: uuid.UUID,
        message_content: str,
        phone_id: Optional[uuid.UUID] = None,
        dtmf_responses: Optional[List[dict]] = None,
        save_as_template: bool = False,
        template_name: Optional[str] = None,
        call_run_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Union[str, bool, List[str]]]:
        """
        Make a custom call with specific content.
        
        Args:
            contact_id: Contact ID to call
            message_content: Message content to use
            phone_id: Specific phone ID to call (optional)
            dtmf_responses: DTMF response configuration (optional)
            save_as_template: Whether to save as template
            template_name: Name for the template
            call_run_id: Call run ID to associate with
            
        Returns:
            Dictionary with results
        """
        result = {
            "success": False,
            "contact_id": str(contact_id),
            "errors": []
        }
        
        # Get contact
        contact_objects = self.repository.get_contacts_by_ids([contact_id])
        if not contact_objects:
            error = f"Contact with ID {contact_id} not found"
            logger.error(error)
            result["errors"].append(error)
            return result
            
        contact = contact_objects[0]
        
        # Create message template if requested
        message_id = None
        if save_as_template and template_name:
            try:
                template = self.repository.create_template_message(
                    name=template_name,
                    content=message_content,
                    message_type="voice"
                )
                message_id = template.id
                logger.info(f"Created new message template: {template_name} with ID {message_id}")
                result["template_id"] = str(message_id)
            except Exception as e:
                error = f"Failed to create template: {str(e)}"
                logger.error(error)
                result["errors"].append(error)
                # Continue anyway, just won't save as template
        
        # Convert DTMF responses to format expected by CustomMessageLog
        dtmf_config = {}
        if dtmf_responses:
            dtmf_config = {item.get('digit'): {
                'description': item.get('description', ''),
                'response_message': item.get('response_message', '')
            } for item in dtmf_responses}
            
        # Create custom message log
        custom_message = self.repository.create_custom_message_log(
            message_content=message_content,
            contact_id=contact_id,
            dtmf_responses=dtmf_config
        )
        
        # Determine which phone to use
        phones_to_try = []
        if phone_id:
            # Look for specific number
            for phone in contact.phone_numbers:
                if phone.id == phone_id:
                    phones_to_try = [phone]
                    break
                    
            if not phones_to_try:
                error = f"Phone number with ID {phone_id} not found for contact {contact.name}"
                logger.error(error)
                result["errors"].append(error)
                return result
        else:
            # Use all numbers in priority order
            phones_to_try = sorted(contact.phone_numbers, key=lambda p: p.priority)
            
        if not phones_to_try:
            error = f"No phone numbers found for contact {contact.name}"
            logger.error(error)
            result["errors"].append(error)
            return result
            
        # Make the calls
        for idx, phone in enumerate(phones_to_try):
            try:
                logger.info(f"Making custom call to {contact.name} at {phone.number}")
                
                # Create call log
                call_log = self.repository.create_call_log(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    call_sid="pending",
                    status="custom",
                    message_id=message_id,
                    custom_message_log_id=custom_message.id,
                    call_run_id=call_run_id
                )
                
                # Update call run stats if needed
                if call_run_id:
                    self.repository.update_call_run_stats(call_run_id)
                
                # Make the call
                call_sid = self.make_twilio_call(
                    to_number=phone.number,
                    custom_message_id=custom_message.id
                )
                
                # Update call log
                call_log.call_sid = call_sid
                self.repository.update_call_log(call_log)
                
                # Wait for answer
                answered = await self._wait_for_answer(call_sid)
                
                if answered:
                    logger.info(f"Custom call to {contact.name} was answered")
                    result["success"] = True
                    
                    # Update call run stats if needed
                    if call_run_id:
                        self.repository.update_call_run_stats(call_run_id)
                        
                    return result
                else:
                    logger.warning(f"Custom call to {contact.name} was not answered")
                    
                    # Update log status
                    call_log.status = "no-answer"
                    self.repository.update_call_log(call_log)
                    
                    # Update call run stats if needed
                    if call_run_id:
                        self.repository.update_call_run_stats(call_run_id)
                        
                    # Try next number if available
                    if idx < len(phones_to_try) - 1:
                        await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
                        
            except Exception as e:
                error = f"Error making custom call to {contact.name}: {str(e)}"
                logger.error(error, exc_info=True)
                result["errors"].append(error)
                
                # Update log status if we created one
                if 'call_log' in locals():
                    call_log.status = "error"
                    self.repository.update_call_log(call_log)
                    
                    # Update call run stats if needed
                    if call_run_id:
                        self.repository.update_call_run_stats(call_run_id)
                        
                # Try next number if available
                if idx < len(phones_to_try) - 1:
                    await asyncio.sleep(settings.SECONDARY_BACKOFF_SEC)
                    
        # All attempts failed
        result["success"] = False
        if not result["errors"]:
            result["errors"].append(f"Failed to call {contact.name} on all numbers")
            
        return result