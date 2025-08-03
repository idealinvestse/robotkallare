"""Call orchestration service for coordinating multiple contact calls.

This service orchestrates the process of calling multiple contacts,
managing the workflow and coordination between different services.
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Union, Any

from sqlmodel import Session

from app.models import Contact, Message, CustomMessageLog
from app.repositories.call_repository import CallRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.message_repository import MessageRepository
from app.services.twilio_call_service import TwilioCallService
from app.services.call_run_service import CallRunService
from app.config import get_settings

logger = logging.getLogger(__name__)


class CallResult:
    """Result object for call operations."""
    
    def __init__(self):
        self.status = "success"
        self.total_contacts = 0
        self.completed_calls = 0
        self.answered_calls = 0
        self.errors = []
        self.call_run_id = None
        self.success = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "status": self.status,
            "total_contacts": self.total_contacts,
            "completed_calls": self.completed_calls,
            "answered_calls": self.answered_calls,
            "errors": self.errors,
            "call_run_id": str(self.call_run_id) if self.call_run_id else None,
            "success": self.success
        }


class CallOrchestrationService:
    """Service for orchestrating calls to multiple contacts.
    
    This service coordinates the calling process, managing the workflow
    between contact retrieval, call execution, and result tracking.
    """
    
    def __init__(
        self, 
        session: Session,
        twilio_service: Optional[TwilioCallService] = None,
        call_run_service: Optional[CallRunService] = None
    ):
        """Initialize with required services.
        
        Args:
            session: Database session
            twilio_service: Optional Twilio service (for testing)
            call_run_service: Optional call run service (for testing)
        """
        self.session = session
        self.settings = get_settings()
        
        # Initialize repositories
        self.call_repository = CallRepository(session)
        self.contact_repository = ContactRepository(session)
        self.message_repository = MessageRepository(session)
        
        # Initialize services
        self.twilio_service = twilio_service or TwilioCallService()
        self.call_run_service = call_run_service or CallRunService(session)
    
    async def dial_contacts(
        self,
        contact_ids: Optional[Sequence[uuid.UUID]] = None,
        group_id: Optional[uuid.UUID] = None,
        message_id: Optional[uuid.UUID] = None,
        call_run_name: Optional[str] = None,
        call_run_description: Optional[str] = None,
        existing_call_run_id: Optional[uuid.UUID] = None
    ) -> CallResult:
        """Orchestrate calling multiple contacts.
        
        Args:
            contact_ids: Specific contact IDs to call
            group_id: Group ID to call all members
            message_id: Message ID to use for calls
            call_run_name: Name for a new call run
            call_run_description: Description for a new call run
            existing_call_run_id: ID of an existing call run
            
        Returns:
            CallResult with operation results
        """
        result = CallResult()
        
        try:
            # Get contacts to call
            contacts = await self._get_contacts_for_calling(contact_ids, group_id)
            if not contacts:
                result.status = "error"
                result.errors.append("No contacts found to dial")
                return result
            
            result.total_contacts = len(contacts)
            
            # Get or create call run
            call_run = await self._get_or_create_call_run(
                existing_call_run_id, call_run_name, call_run_description, 
                message_id, group_id
            )
            result.call_run_id = call_run.id
            
            # Execute calls
            await self._execute_contact_calls(contacts, message_id, call_run.id, result)
            
            # Update final statistics
            self.call_run_service.update_call_run_stats(call_run.id)
            
            # Mark call run as completed if all calls are done
            if result.completed_calls == result.total_contacts:
                self.call_run_service.complete_call_run(call_run.id)
            
            result.success = result.answered_calls > 0
            
        except Exception as e:
            logger.error(f"Error in dial_contacts orchestration: {e}", exc_info=True)
            result.status = "error"
            result.errors.append(f"Orchestration error: {str(e)}")
        
        return result
    
    async def make_manual_call(
        self,
        contact_id: uuid.UUID,
        message_id: uuid.UUID,
        phone_id: Optional[uuid.UUID] = None,
        call_run_id: Optional[uuid.UUID] = None
    ) -> CallResult:
        """Make a manual call to a specific contact.
        
        Args:
            contact_id: Contact ID to call
            message_id: Message ID to use
            phone_id: Specific phone ID to use (optional)
            call_run_id: Optional call run ID
            
        Returns:
            CallResult with operation results
        """
        result = CallResult()
        
        try:
            # Get contact
            contact = self.contact_repository.get_by_id(contact_id)
            if not contact:
                result.status = "error"
                result.errors.append(f"Contact {contact_id} not found")
                return result
            
            result.total_contacts = 1
            
            # Execute single contact call
            success = await self._dial_single_contact(
                contact, message_id, call_run_id, phone_id
            )
            
            if success:
                result.completed_calls = 1
                result.answered_calls = 1
                result.success = True
            else:
                result.errors.append(f"Failed to call {contact.name}")
            
        except Exception as e:
            logger.error(f"Error in make_manual_call: {e}", exc_info=True)
            result.status = "error"
            result.errors.append(f"Manual call error: {str(e)}")
        
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
    ) -> CallResult:
        """Make a custom call with specific content.
        
        Args:
            contact_id: Contact ID to call
            message_content: Custom message content
            phone_id: Specific phone ID to call (optional)
            dtmf_responses: Optional DTMF responses
            save_as_template: Whether to save as template
            template_name: Template name if saving
            call_run_id: Optional call run ID
            
        Returns:
            CallResult with operation results
        """
        result = CallResult()
        
        try:
            # Get contact
            contact = self.contact_repository.get_by_id(contact_id)
            if not contact:
                result.status = "error"
                result.errors.append(f"Contact {contact_id} not found")
                return result
            
            result.total_contacts = 1
            
            # Create custom message log
            custom_message = CustomMessageLog(
                contact_id=contact_id,
                message_content=message_content,
                message_type="call",
                dtmf_responses=dtmf_responses
            )
            
            self.session.add(custom_message)
            self.session.commit()
            self.session.refresh(custom_message)
            
            # Save as template if requested
            if save_as_template and template_name:
                await self._save_as_template(template_name, message_content, dtmf_responses)
            
            # Execute custom call
            success = await self._dial_single_contact_custom(
                contact, custom_message.id, call_run_id, phone_id
            )
            
            if success:
                result.completed_calls = 1
                result.answered_calls = 1
                result.success = True
            else:
                result.errors.append(f"Failed to make custom call to {contact.name}")
            
        except Exception as e:
            logger.error(f"Error in make_custom_call: {e}", exc_info=True)
            result.status = "error"
            result.errors.append(f"Custom call error: {str(e)}")
        
        return result
    
    async def _get_contacts_for_calling(
        self, 
        contact_ids: Optional[Sequence[uuid.UUID]], 
        group_id: Optional[uuid.UUID]
    ) -> List[Contact]:
        """Get contacts for calling based on parameters."""
        if contact_ids:
            return self.contact_repository.get_contacts_by_ids(list(contact_ids))
        elif group_id:
            return self.contact_repository.get_contacts_by_group_id(group_id)
        else:
            return self.contact_repository.get_all_contacts()
    
    async def _get_or_create_call_run(
        self,
        existing_call_run_id: Optional[uuid.UUID],
        call_run_name: Optional[str],
        call_run_description: Optional[str],
        message_id: Optional[uuid.UUID],
        group_id: Optional[uuid.UUID]
    ):
        """Get existing call run or create a new one."""
        if existing_call_run_id:
            call_run = self.call_run_service.get_call_run(existing_call_run_id)
            if not call_run:
                raise ValueError(f"Call run with ID {existing_call_run_id} not found")
            return call_run
        else:
            name = call_run_name or f"Call Run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self.call_run_service.create_call_run(
                name=name,
                description=call_run_description,
                message_id=message_id,
                group_id=group_id
            )
    
    async def _execute_contact_calls(
        self, 
        contacts: List[Contact], 
        message_id: Optional[uuid.UUID], 
        call_run_id: uuid.UUID, 
        result: CallResult
    ):
        """Execute calls to all contacts."""
        for contact in contacts:
            try:
                success = await self._dial_single_contact(contact, message_id, call_run_id)
                result.completed_calls += 1
                
                if success:
                    result.answered_calls += 1
                
                # Update call run stats periodically
                self.call_run_service.update_call_run_stats(call_run_id)
                
            except Exception as e:
                error_msg = f"Error calling {contact.name}: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
    
    async def _dial_single_contact(
        self,
        contact: Contact,
        message_id: Optional[uuid.UUID] = None,
        call_run_id: Optional[uuid.UUID] = None,
        phone_id: Optional[uuid.UUID] = None,
        custom_message_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Dial a single contact, trying each number in priority order."""
        # Get phone numbers to try
        if phone_id:
            phones_to_try = [phone for phone in contact.phone_numbers if phone.id == phone_id]
        else:
            phones_to_try = sorted(contact.phone_numbers, key=lambda p: p.priority)
        
        if not phones_to_try:
            logger.warning(f"No phone numbers found for contact {contact.name}")
            return False
        
        # Try each phone number
        for idx, phone in enumerate(phones_to_try):
            try:
                # Build callback URL
                base_url = self.settings.PUBLIC_URL or f"http://{self.settings.API_HOST}:{self.settings.API_PORT}"
                callback_url = self.twilio_service.build_callback_url(
                    base_url, message_id, custom_message_id
                )
                status_callback_url = self.twilio_service.build_status_callback_url(base_url)
                
                # Create call log
                call_log = self.call_repository.create_call_log(
                    contact_id=contact.id,
                    phone_number_id=phone.id,
                    call_sid="pending",
                    status="initiated",
                    message_id=message_id,
                    custom_message_log_id=custom_message_id,
                    call_run_id=call_run_id
                )
                
                # Make the call
                call_sid = self.twilio_service.create_call(
                    to_number=phone.number,
                    callback_url=callback_url,
                    status_callback_url=status_callback_url
                )
                
                # Update call log with SID
                call_log.call_sid = call_sid
                self.call_repository.update_call_log(call_log)
                
                # Wait for answer
                answered = await self._wait_for_answer(call_sid)
                
                if answered:
                    logger.info(f"Call to {contact.name} at {phone.number} was answered")
                    return True
                else:
                    logger.warning(f"Call to {contact.name} at {phone.number} was not answered")
                    
                    # Update log status
                    call_log.status = "no-answer"
                    self.call_repository.update_call_log(call_log)
                    
                    # Try next number if available
                    if idx < len(phones_to_try) - 1:
                        await asyncio.sleep(self.settings.SECONDARY_BACKOFF_SEC)
                
            except Exception as e:
                logger.error(f"Error calling {contact.name} at {phone.number}: {e}")
                
                # Update log status if we created one
                if 'call_log' in locals():
                    call_log.status = "error"
                    self.call_repository.update_call_log(call_log)
                
                # Try next number if available
                if idx < len(phones_to_try) - 1:
                    await asyncio.sleep(self.settings.SECONDARY_BACKOFF_SEC)
        
        return False
    
    async def _dial_single_contact_custom(
        self,
        contact: Contact,
        custom_message_id: uuid.UUID,
        call_run_id: Optional[uuid.UUID] = None,
        phone_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Dial a single contact with custom message."""
        return await self._dial_single_contact(
            contact=contact,
            message_id=None,
            call_run_id=call_run_id,
            phone_id=phone_id,
            custom_message_id=custom_message_id
        )
    
    async def _wait_for_answer(self, call_sid: str, timeout: int = 30) -> bool:
        """Wait for a call to be answered."""
        try:
            for _ in range(timeout):
                call_status = self.twilio_service.get_call_status(call_sid)
                
                if call_status["status"] in ["completed", "busy", "no-answer", "failed", "canceled"]:
                    return call_status["status"] == "completed" and call_status.get("answered_by") is not None
                
                await asyncio.sleep(1)
            
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for call answer {call_sid}: {e}")
            return False
    
    async def _save_as_template(
        self, 
        template_name: str, 
        message_content: str, 
        dtmf_responses: Optional[List[dict]]
    ):
        """Save custom message as a template."""
        try:
            template_message = Message(
                name=template_name,
                content=message_content,
                is_template=True,
                message_type="voice"
            )
            
            self.session.add(template_message)
            self.session.commit()
            
            logger.info(f"Saved custom message as template: {template_name}")
            
        except Exception as e:
            logger.error(f"Error saving template {template_name}: {e}")
            # Don't raise - template saving is optional
