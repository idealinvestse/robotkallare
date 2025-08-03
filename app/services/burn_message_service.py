"""Service for creating and managing burn messages (read-once messages)."""
import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any

from sqlmodel import Session, select
from fastapi import HTTPException

from app.config import get_settings
from app.models import BurnMessage, Contact, Message, DtmfResponse
from app.repositories.sms_repository import SmsRepository

logger = logging.getLogger(__name__)
settings = get_settings()

class BurnMessageService:
    """Service for burn message operations."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.sms_repository = SmsRepository(session)
        
    def get_dialer_service(self):
        """Get the dialer service instance (lazy import to avoid circular imports)."""
        from app.dialer import DialerService
        return DialerService(self.session)
        
    def generate_token(self) -> str:
        """Generate a secure, unique token for the burn message URL."""
        # Generate a random token
        random_token = secrets.token_hex(16)
        
        # Add a timestamp component for uniqueness
        timestamp = datetime.now().timestamp()
        
        # Hash the combined values
        hash_input = f"{random_token}:{timestamp}"
        token_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:20]
        
        return token_hash
        
    def create_burn_message(
        self, 
        content: str, 
        expires_in_hours: int = 24,
        created_by_contact_id: Optional[uuid.UUID] = None
    ) -> BurnMessage:
        """Create a new burn message that expires after the specified time.
        
        Args:
            content: The message content
            expires_in_hours: Hours until the message expires
            created_by_contact_id: Optional ID of the contact who created the message
            
        Returns:
            The created BurnMessage object
        """
        # Generate a unique token
        token = self.generate_token()
        
        # Calculate expiration time
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        # Create burn message
        burn_message = BurnMessage(
            token=token,
            content=content,
            created_at=datetime.now(),
            expires_at=expires_at,
            viewed=False,
            created_by_contact_id=created_by_contact_id
        )
        
        self.session.add(burn_message)
        self.session.commit()
        self.session.refresh(burn_message)
        
        logger.info(f"Created burn message with token {token}, expires at {expires_at}")
        return burn_message
        
    def get_burn_message(self, token: str, mark_as_viewed: bool = True) -> Optional[BurnMessage]:
        """Get a burn message by token and optionally mark it as viewed.
        
        Args:
            token: The unique token for the message
            mark_as_viewed: Whether to mark the message as viewed
            
        Returns:
            The BurnMessage if found and not expired, None otherwise
        """
        try:
            message = self.session.exec(
                select(BurnMessage).where(BurnMessage.token == token)
            ).first()
            
            if not message:
                logger.warning(f"Burn message with token {token} not found")
                return None
                
            # Check if message has expired
            if message.expires_at < datetime.now():
                logger.warning(f"Burn message with token {token} has expired")
                # Delete expired message
                try:
                    self.session.delete(message)
                    self.session.commit()
                    logger.info(f"Deleted expired burn message with token {token}")
                except Exception as e:
                    logger.error(f"Failed to delete expired burn message {token}: {str(e)}", exc_info=True)
                    self.session.rollback()
                return None
                
            # Check if message has already been viewed
            if message.viewed:
                logger.warning(f"Burn message with token {token} has already been viewed")
                return None
                
            # Mark as viewed if requested
            if mark_as_viewed:
                try:
                    message.viewed = True
                    message.viewed_at = datetime.now()
                    self.session.add(message)
                    self.session.commit()
                    self.session.refresh(message)
                    logger.info(f"Marked burn message with token {token} as viewed")
                except Exception as e:
                    # If we can't mark as viewed, log the error but still return the message
                    logger.error(f"Failed to mark burn message {token} as viewed: {str(e)}", exc_info=True)
                    self.session.rollback()  # Rollback the failed transaction
                
            return message
        except Exception as e:
            logger.error(f"Error retrieving burn message with token {token}: {str(e)}", exc_info=True)
            self.session.rollback()  # Ensure the session is cleaned up
            return None
        
    def clean_expired_messages(self) -> int:
        """Delete all expired and viewed burn messages.
        
        Returns:
            Number of messages deleted
        """
        # Get all expired or viewed messages
        current_time = datetime.now()
        expired_messages = self.session.exec(
            select(BurnMessage).where(
                (BurnMessage.expires_at < current_time) | 
                (BurnMessage.viewed == True)
            )
        ).all()
        
        # Delete them
        count = 0
        for message in expired_messages:
            self.session.delete(message)
            count += 1
            
        self.session.commit()
        logger.info(f"Deleted {count} expired or viewed burn messages")
        return count
        
    def get_burn_message_url(self, token: str, base_url: Optional[str] = None) -> str:
        """Get the full URL for a burn message.
        
        Args:
            token: The unique token for the message
            base_url: Optional base URL to use (defaults to settings)
            
        Returns:
            The full URL to access the burn message
        """
        if not base_url:
            base_url = settings.BASE_URL
            
        # Make sure base_url doesn't end with a slash
        if base_url.endswith('/'):
            base_url = base_url[:-1]
            
        return f"{base_url}/burn/{token}"
        
    async def send_burn_message_sms(
        self, 
        message_content: str, 
        burn_content: str,
        recipients: Optional[List[uuid.UUID]] = None,
        group_id: Optional[uuid.UUID] = None,
        custom_link_text: Optional[str] = None,
        expires_in_hours: int = 24,
        base_url: Optional[str] = None
    ) -> Dict:
        """Create a burn message and send an SMS with a link to it.
        
        Args:
            message_content: The SMS message content
            burn_content: The content to store in the burn message
            recipients: Optional list of contact IDs to send to
            group_id: Optional group ID to send to everyone in the group
            custom_link_text: Optional custom text for the link
            expires_in_hours: Hours until the message expires
            base_url: Optional base URL for burn message links
            
        Returns:
            Dict with results of the operation
        """
        result = {
            "status": "success",
            "sent_count": 0,
            "failed_count": 0,
            "errors": []
        }
        
        try:
            # Validate inputs
            if not burn_content:
                error = "Burn content cannot be empty"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            if not message_content:
                error = "SMS message content cannot be empty"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            if not recipients and not group_id:
                error = "Either recipients or group_id must be provided"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            # Create the burn message
            burn_message = self.create_burn_message(
                content=burn_content,
                expires_in_hours=expires_in_hours
            )
            
            # Get the URL for the burn message
            burn_url = self.get_burn_message_url(burn_message.token, base_url)
            
            # Prepare the SMS message with the burn link
            link_text = custom_link_text or "View sensitive message (link expires after viewing)"
            full_message = f"{message_content}\n\n{link_text}:\n{burn_url}"
            
            # Get contacts
            contacts = []
            if recipients:
                contacts = self.sms_repository.get_contacts_by_ids(recipients)
            elif group_id:
                contacts = self.sms_repository.get_contacts_by_group_id(group_id)
                
            # Create a temporary message object for _send_to_contact
            from app.models import Message
            temp_message = Message(
                id=None,
                name="Burn SMS",
                content=full_message,
                is_template=False,
                message_type="sms"
            )
            
            # Send to each contact using the SmsService
            from app.services.sms_service import SmsService
            sms_service = SmsService(self.session)
            
            for contact in contacts:
                success = await sms_service._send_to_contact(
                    contact=contact,
                    message=temp_message
                )
                
                if success:
                    result["sent_count"] += 1
                else:
                    result["failed_count"] += 1
                    
            if result["sent_count"] == 0:
                result["status"] = "error"
                result["errors"].append("Failed to send SMS to any recipients")
                
            logger.info(f"Burn message SMS sending completed: {result['sent_count']} sent, {result['failed_count']} failed")
            return result
            
        except Exception as e:
            error = f"Error sending burn message SMS: {str(e)}"
            logger.error(error, exc_info=True)
            result["status"] = "error"
            result["errors"].append(error)
            return result
            
    async def initiate_burn_message_call(
        self, 
        burn_content: str,
        intro_message: str,
        recipients: Optional[List[uuid.UUID]] = None,
        group_id: Optional[uuid.UUID] = None,
        custom_link_text: Optional[str] = None,
        dtmf_digit: str = "1",
        dtmf_message: Optional[str] = None,
        expires_in_hours: int = 24,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a burn message and initiate voice calls to direct recipients to it.
        
        Args:
            burn_content: Content to store in the burn message
            intro_message: What the voice robot should say
            recipients: Optional list of contact IDs to call
            group_id: Optional group ID to call everyone in the group
            custom_link_text: Optional custom text for the SMS link
            dtmf_digit: DTMF digit to press to confirm
            dtmf_message: Message to say when DTMF is pressed
            expires_in_hours: Hours until the message expires
            base_url: Optional base URL for burn message links
            
        Returns:
            Dict with results of the operation
        """
        result = {
            "status": "success",
            "call_count": 0,
            "errors": []
        }
        
        try:
            # Validate inputs
            if not burn_content:
                error = "Burn content cannot be empty"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            if not intro_message:
                error = "Intro message cannot be empty"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            if not recipients and not group_id:
                error = "Either recipients or group_id must be provided"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            # Create the burn message
            burn_message = self.create_burn_message(
                content=burn_content,
                expires_in_hours=expires_in_hours
            )
            
            # Get the URL for the burn message
            burn_url = self.get_burn_message_url(burn_message.token, base_url)
            
            # Prepare the SMS message with the burn link
            link_text = custom_link_text or "Visa det hemliga meddelandet (länken fungerar bara en gång)"
            sms_text = f"{intro_message}\n\n{link_text}:\n{burn_url}"
            
            # Prepare DTMF response if provided
            if dtmf_digit and dtmf_message:
                # Check if a response for this digit already exists
                dtmf_response = self.session.exec(
                    select(DtmfResponse).where(DtmfResponse.digit == dtmf_digit)
                ).first()
                
                # Create or update DTMF response
                if not dtmf_response:
                    dtmf_response = DtmfResponse(
                        digit=dtmf_digit,
                        description=f"Burn message confirmation for {dtmf_digit}",
                        response_message=dtmf_message,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.session.add(dtmf_response)
                else:
                    dtmf_response.response_message = dtmf_message
                    dtmf_response.updated_at = datetime.now()
                    self.session.add(dtmf_response)
                
                self.session.commit()
            
            # Get contacts
            contacts = []
            if recipients:
                contacts = self.sms_repository.get_contacts_by_ids(recipients)
            elif group_id:
                contacts = self.sms_repository.get_contacts_by_group_id(group_id)
                
            if not contacts:
                error = "No valid contacts found"
                logger.error(error)
                result["errors"].append(error)
                result["status"] = "error"
                return result
                
            # Create a message for the intro
            temp_message = Message(
                id=None,
                name="Burn Message Call",
                content=intro_message,
                is_template=False,
                message_type="voice"
            )
            
            # Create a message for the SMS
            sms_message = Message(
                id=None,
                name="Burn Message SMS",
                content=sms_text,
                is_template=False,
                message_type="sms"
            )
            
            # Get the dialer service
            dialer_service = self.get_dialer_service()
            
            # Track the burn message ID in the call log for reference
            custom_data = {
                "burn_message_id": str(burn_message.id),
                "burn_message_token": burn_message.token,
                "send_sms_on_dtmf": dtmf_digit
            }
            
            # Initiate the calls
            # Extract contact IDs from the Contact objects
            contact_ids = [contact.id for contact in contacts]
            
            call_results = await dialer_service.start_call_run(
                contacts=contact_ids,
                message=temp_message,
                group_id=group_id,
                name=f"Burn Message Call - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description=f"Voice call for burn message {burn_message.token}",
                dtmf_confirmations=True,
                custom_data=custom_data,
                sms_after_dtmf=sms_message
            )
            
            # Update the result
            result["call_count"] = call_results.get("total_calls", 0)
            result["call_run_id"] = str(call_results.get("call_run_id"))
            
            if result["call_count"] == 0:
                result["status"] = "error"
                result["errors"].append("Failed to initiate any calls")
            
            logger.info(f"Burn message call run initiated: {result['call_count']} calls scheduled")
            return result
            
        except Exception as e:
            error = f"Error initiating burn message calls: {str(e)}"
            logger.error(error, exc_info=True)
            result["status"] = "error"
            result["errors"].append(error)
            return result