"""Call repository for database operations related to phone calls."""
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import (
    Contact, PhoneNumber, CallLog, Message, CustomMessageLog,
    GroupContactLink, CallRun
)

logger = logging.getLogger(__name__)

class CallRepository:
    """Repository for call-related database operations."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    def get_message_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """Get a message by ID."""
        return self.session.exec(
            select(Message).where(Message.id == message_id)
        ).first()
    
    def get_contacts_by_ids(self, contact_ids: Sequence[uuid.UUID]) -> List[Contact]:
        """Get contacts by IDs with their phone numbers."""
        return self.session.exec(
            select(Contact)
            .where(Contact.id.in_(contact_ids))
            .options(selectinload(Contact.phone_numbers))
        ).all()
    
    def get_contacts_by_group_id(self, group_id: uuid.UUID) -> List[Contact]:
        """Get all contacts in a group with their phone numbers."""
        # Get contact IDs in this group
        contact_links = self.session.exec(
            select(GroupContactLink).where(GroupContactLink.group_id == group_id)
        ).all()
        
        contact_ids = [link.contact_id for link in contact_links]
        if not contact_ids:
            return []
        
        # Get contacts with phone numbers
        return self.session.exec(
            select(Contact)
            .where(Contact.id.in_(contact_ids))
            .options(selectinload(Contact.phone_numbers))
        ).all()
    
    def get_all_contacts(self) -> List[Contact]:
        """Get all contacts with their phone numbers."""
        return self.session.exec(
            select(Contact).options(selectinload(Contact.phone_numbers))
        ).all()
    
    def get_call_run(self, call_run_id: uuid.UUID) -> Optional[CallRun]:
        """Get a call run by ID."""
        return self.session.exec(
            select(CallRun).where(CallRun.id == call_run_id)
        ).first()
    
    def create_call_run(
        self,
        name: str,
        description: Optional[str] = None,
        message_id: Optional[uuid.UUID] = None,
        group_id: Optional[uuid.UUID] = None,
        total_calls: int = 0
    ) -> CallRun:
        """Create a new call run."""
        call_run = CallRun(
            name=name,
            description=description,
            message_id=message_id,
            group_id=group_id,
            status="in_progress",
            total_calls=total_calls,
            started_at=datetime.now()
        )
        self.session.add(call_run)
        self.session.commit()
        self.session.refresh(call_run)
        return call_run
    
    def update_call_run(self, call_run: CallRun) -> CallRun:
        """Update a call run."""
        self.session.add(call_run)
        self.session.commit()
        self.session.refresh(call_run)
        return call_run
    
    def update_call_run_stats(self, call_run_id: uuid.UUID) -> Optional[CallRun]:
        """Update statistics for a call run."""
        call_run = self.get_call_run(call_run_id)
        if not call_run:
            logger.error(f"Call run with ID {call_run_id} not found when updating stats")
            return None
            
        # Get updated counts
        total_calls = self.session.exec(
            select(CallLog).where(CallLog.call_run_id == call_run_id)
        ).count()
        
        completed_calls = self.session.exec(
            select(CallLog).where(
                (CallLog.call_run_id == call_run_id) & 
                (CallLog.status.in_(["completed", "no-answer", "manual", "error"]))
            )
        ).count()
        
        answered_calls = self.session.exec(
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
            
        return self.update_call_run(call_run)
    
    def create_call_log(
        self,
        contact_id: uuid.UUID,
        phone_number_id: uuid.UUID,
        call_sid: str,
        status: str,
        answered: bool = False,
        digits: Optional[str] = None,
        message_id: Optional[uuid.UUID] = None,
        custom_message_log_id: Optional[uuid.UUID] = None,
        scheduled_message_id: Optional[uuid.UUID] = None,
        call_run_id: Optional[uuid.UUID] = None
    ) -> CallLog:
        """Create and save a call log entry."""
        log = CallLog(
            contact_id=contact_id,
            phone_number_id=phone_number_id,
            call_sid=call_sid,
            started_at=datetime.now(),
            answered=answered,
            digits=digits,
            status=status,
            message_id=message_id,
            custom_message_log_id=custom_message_log_id,
            scheduled_message_id=scheduled_message_id,
            call_run_id=call_run_id
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log
    
    def update_call_log(self, call_log: CallLog) -> CallLog:
        """Update a call log entry."""
        self.session.add(call_log)
        self.session.commit()
        self.session.refresh(call_log)
        return call_log
    
    def get_call_log_by_sid(self, call_sid: str) -> Optional[CallLog]:
        """Get a call log entry by its Twilio CallSid."""
        return self.session.exec(
            select(CallLog).where(CallLog.call_sid == call_sid)
        ).first()

    def get_call_log_by_sid(self, call_sid: str) -> Optional[CallLog]:
        """Get a call log entry by its Twilio CallSid."""
        return self.session.exec(
            select(CallLog).where(CallLog.call_sid == call_sid)
        ).first()

    def create_call_log(
        self,
        contact_id: uuid.UUID,
        phone_number_id: uuid.UUID,
        call_sid: str,
        status: str,
        answered: bool = False,
        digits: Optional[str] = None,
        message_id: Optional[uuid.UUID] = None,
        custom_message_log_id: Optional[uuid.UUID] = None,
        scheduled_message_id: Optional[uuid.UUID] = None,
        call_run_id: Optional[uuid.UUID] = None
    ) -> CallLog:
        """Create and save a call log entry."""
        log = CallLog(
            contact_id=contact_id,
            phone_number_id=phone_number_id,
            call_sid=call_sid,
            started_at=datetime.now(),
            answered=answered,
            digits=digits,
            status=status,
            message_id=message_id,
            custom_message_log_id=custom_message_log_id,
            scheduled_message_id=scheduled_message_id,
            call_run_id=call_run_id
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log
    
    def create_custom_message_log(
        self,
        message_content: str,
        message_type: str = "call",
        contact_id: Optional[uuid.UUID] = None,
        dtmf_responses: Optional[dict] = None
    ) -> CustomMessageLog:
        """Create and save a custom message log entry."""
        log = CustomMessageLog(
            contact_id=contact_id,
            message_content=message_content,
            message_type=message_type,
            dtmf_responses=dtmf_responses,
            created_at=datetime.now()
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log
    
    def create_template_message(
        self, 
        name: str, 
        content: str, 
        message_type: str = "voice"
    ) -> Message:
        """Create a new message template."""
        message = Message(
            name=name,
            content=content,
            is_template=True,
            message_type=message_type,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message
    
    def get_phone_for_contact(
        self, 
        contact: Contact
    ) -> Tuple[List[PhoneNumber], List[str]]:
        """
        Get prioritized phone numbers for a contact.
        Returns a tuple of (phone_objects, error_messages)
        """
        errors = []
        if not contact.phone_numbers:
            errors.append(f"Contact {contact.name} has no phone numbers")
            return [], errors
            
        # Sort by priority
        phones = sorted(contact.phone_numbers, key=lambda p: p.priority)
        return phones, errors