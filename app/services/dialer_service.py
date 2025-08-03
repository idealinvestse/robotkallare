"""Dialer service for voice call operations."""
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlmodel import Session

from app.config import get_settings
from app.models import Contact, Message, CallRun, CallLog
from app.repositories.call_repository import CallRepository
from app.repositories.contact_repository import ContactRepository
from app.services.twilio_call_service import TwilioCallService

logger = logging.getLogger(__name__)
settings = get_settings()


class DialerService:
    """Service for initiating voice calls with proper separation of concerns."""
    
    def __init__(self, session: Session):
        """Initialize with database session and dependencies."""
        self.session = session
        self.call_repository = CallRepository(session)
        self.contact_repository = ContactRepository(session)
        self.twilio_service = TwilioCallService()
    
    async def start_call_run(
        self, 
        contacts: List[uuid.UUID] = None,
        message: Optional[Message] = None,
        group_id: Optional[uuid.UUID] = None,
        name: str = "Call Run",
        description: Optional[str] = None,
        dtmf_confirmations: bool = False,
        custom_data: Optional[Dict[str, Any]] = None,
        sms_after_dtmf: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a call run and initiate calls to multiple contacts.
        
        Args:
            contacts: List of contact IDs to call
            message: Message object or message ID to use
            group_id: Optional group ID if calling a group
            name: Name for the call run
            description: Optional description
            dtmf_confirmations: Whether to use DTMF for confirmation
            custom_data: Any custom data to associate with calls
            sms_after_dtmf: Message to send as SMS after DTMF confirmation
            
        Returns:
            Dictionary with call run results
        """
        logger.info(f"Starting call run: {name}")
        
        try:
            # Create a new call run
            call_run = CallRun(
                name=name,
                description=description,
                message_id=message.id if hasattr(message, 'id') else None,
                group_id=group_id,
                status="in_progress",
                total_calls=len(contacts) if contacts else 0,
                started_at=datetime.now(),
                custom_data=custom_data
            )
            self.session.add(call_run)
            self.session.commit()
            self.session.refresh(call_run)
            
            # Handle message preparation
            message_id = await self._prepare_message(message, name)
            
            # Import here to avoid circular dependencies
            from app.workers.call_worker import dial_contacts_worker
            
            # Delegate to worker for actual calling
            await dial_contacts_worker(
                contacts=contacts,
                group_id=group_id,
                message_id=message_id,
                call_run_id=call_run.id
            )
            
            return {
                "call_run_id": call_run.id,
                "total_calls": len(contacts) if contacts else 0,
                "status": "initiated"
            }
            
        except Exception as e:
            logger.error(f"Error starting call run: {str(e)}", exc_info=True)
            return {
                "call_run_id": None,
                "total_calls": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def dial_contact(
        self, 
        contact_id: uuid.UUID, 
        message_id: uuid.UUID, 
        burn_message_token: Optional[str] = None
    ) -> bool:
        """
        Dial a single contact with a specific message.
        
        Args:
            contact_id: ID of the contact to call
            message_id: ID of the message to use for the call
            burn_message_token: Optional token for a burn message
            
        Returns:
            True if the call was successful (initiated), False otherwise
        """
        try:
            # Get contact with phone numbers
            contact = self.contact_repository.get_contact_with_phones(contact_id)
            if not contact:
                logger.error(f"Contact with ID {contact_id} not found")
                return False
            
            # Get message
            message = self.session.get(Message, message_id)
            if not message:
                logger.error(f"Message with ID {message_id} not found")
                return False
            
            # Delegate to call worker for actual dialing
            from app.workers.call_worker import dial_single_contact_worker
            return await dial_single_contact_worker(
                contact=contact,
                message_id=message_id,
                burn_message_token=burn_message_token
            )
            
        except Exception as e:
            logger.error(f"Error dialing contact {contact_id}: {str(e)}", exc_info=True)
            return False
    
    async def _prepare_message(self, message: Any, call_run_name: str) -> Optional[uuid.UUID]:
        """
        Prepare message for calling - handle both Message objects and content.
        
        Args:
            message: Message object or content
            call_run_name: Name of the call run for temporary messages
            
        Returns:
            Message ID to use for calling
        """
        if not message:
            return None
            
        # If message has an ID, use it directly
        if hasattr(message, 'id') and message.id:
            return message.id
            
        # If message has content, create a temporary message
        if hasattr(message, 'content'):
            temp_message = Message(
                name=f"Temp-{call_run_name}",
                content=message.content,
                is_template=False,
                message_type="voice",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.session.add(temp_message)
            self.session.commit()
            self.session.refresh(temp_message)
            return temp_message.id
            
        return None
    
    def get_call_run_stats(self, call_run_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get statistics for a call run.
        
        Args:
            call_run_id: ID of the call run
            
        Returns:
            Dictionary with call run statistics
        """
        return self.call_repository.get_call_run_stats(call_run_id)
    
    def update_call_run_status(self, call_run_id: uuid.UUID, status: str) -> bool:
        """
        Update the status of a call run.
        
        Args:
            call_run_id: ID of the call run
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            call_run = self.session.get(CallRun, call_run_id)
            if call_run:
                call_run.status = status
                call_run.updated_at = datetime.now()
                self.session.add(call_run)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating call run status: {str(e)}", exc_info=True)
            return False
