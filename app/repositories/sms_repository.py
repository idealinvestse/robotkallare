"""SMS repository for database operations related to SMS messages."""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Tuple, Union

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import (
    Contact, PhoneNumber, SmsLog, Message, CustomMessageLog,
    GroupContactLink, ScheduledMessage, ScheduledMessageContactLink
)

logger = logging.getLogger(__name__)

class SmsRepository:
    """Repository for SMS-related database operations."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    def get_message_by_id(self, message_id: Union[uuid.UUID, str]) -> Optional[Message]:
        """Get a message by ID."""
        logger.debug(f"Fetching message with ID: {message_id}")
        # Convert string UUID to proper format if needed
        try:
            # Convert to UUID if it's a string
            uuid_value = message_id
            if isinstance(message_id, str):
                try:
                    uuid_value = uuid.UUID(message_id)
                except ValueError as e:
                    logger.error(f"Invalid UUID format for message_id: {message_id}, error: {e}")
                    return None
            
            # Try to find the message with UUID
            statement = select(Message).where(Message.id == uuid_value)
            logger.debug(f"Executing SQL query with UUID: {uuid_value}, type: {type(uuid_value)}")
            try:
                message = self.session.exec(statement).first()
                logger.debug(f"Query executed successfully, result: {message}")
            except Exception as e:
                logger.error(f"Error executing SQL query: {e}, statement: {statement}")
                raise
                
            if message:
                logger.debug(f"Found message: {message.name}, type: {message.message_type}")
            else:
                logger.debug(f"No message found with ID: {message_id}")
            return message
        except Exception as e:
            logger.error(f"Error fetching message with ID {message_id}: {str(e)}")
            return None
    
    def get_contacts_by_ids(self, contact_ids: Sequence[Union[uuid.UUID, str]]) -> List[Contact]:
        """Get contacts by IDs with their phone numbers."""
        logger.debug(f"Fetching contacts by IDs: {contact_ids}")
        
        # Convert string IDs to UUID objects if needed
        uuid_ids = []
        for cid in contact_ids:
            if isinstance(cid, str):
                try:
                    uuid_ids.append(uuid.UUID(cid))
                except ValueError as e:
                    logger.warning(f"Skipping invalid contact ID: {cid}, error: {e}")
            else:
                uuid_ids.append(cid)
        
        if not uuid_ids:
            logger.warning("No valid contact IDs to query")
            return []
            
        try:
            logger.debug(f"Executing query with {len(uuid_ids)} contact IDs")
            contacts = self.session.exec(
                select(Contact)
                .where(Contact.id.in_(uuid_ids))
                .options(selectinload(Contact.phone_numbers))
            ).all()
            logger.debug(f"Found {len(contacts)} contacts by ID lookup")
            return contacts
        except Exception as e:
            logger.error(f"Error fetching contacts by IDs: {e}")
            return []
    
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
    
    def create_sms_log(
        self,
        contact_id: Union[uuid.UUID, str],
        phone_number_id: Union[uuid.UUID, str],
        message_sid: str,
        status: str,
        message_id: Optional[Union[uuid.UUID, str]] = None,
        retry_count: int = 0,
        retry_at: Optional[datetime] = None,
        is_retry: bool = False,
        custom_message_log_id: Optional[Union[uuid.UUID, str]] = None,
        scheduled_message_id: Optional[Union[uuid.UUID, str]] = None
    ) -> SmsLog:
        """Create and save an SMS log entry."""
        # Convert string UUIDs to UUID objects if needed
        uuid_contact_id = self._ensure_uuid(contact_id, "contact_id")
        uuid_phone_id = self._ensure_uuid(phone_number_id, "phone_number_id")
        
        # Convert optional UUIDs
        uuid_message_id = None
        if message_id is not None:
            uuid_message_id = self._ensure_uuid(message_id, "message_id")
            
        uuid_custom_log_id = None
        if custom_message_log_id is not None:
            uuid_custom_log_id = self._ensure_uuid(custom_message_log_id, "custom_message_log_id")
            
        uuid_scheduled_id = None
        if scheduled_message_id is not None:
            uuid_scheduled_id = self._ensure_uuid(scheduled_message_id, "scheduled_message_id")
        
        # Create the log entry with proper UUID objects
        log = SmsLog(
            contact_id=uuid_contact_id,
            phone_number_id=uuid_phone_id,
            message_sid=message_sid,
            sent_at=datetime.utcnow(),
            status=status,
            message_id=uuid_message_id,
            retry_count=retry_count,
            retry_at=retry_at,
            is_retry=is_retry,
            custom_message_log_id=uuid_custom_log_id,
            scheduled_message_id=uuid_scheduled_id
        )
        
        try:
            self.session.add(log)
            self.session.commit()
            self.session.refresh(log)
            return log
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating SMS log: {e}")
            raise
            
    def _ensure_uuid(self, value: Union[uuid.UUID, str], field_name: str) -> uuid.UUID:
        """Convert string UUID to UUID object if needed."""
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError as e:
                logger.error(f"Invalid UUID format for {field_name}: {value}, error: {e}")
                raise ValueError(f"Invalid UUID format for {field_name}: {value}")
        return value
    
    def create_custom_message_log(
        self,
        message_content: str,
        contact_id: Optional[Union[uuid.UUID, str]] = None
    ) -> CustomMessageLog:
        """Create and save a custom message log entry."""
        # Convert string UUID to proper format if needed
        uuid_contact_id = None
        if contact_id:
            if isinstance(contact_id, str):
                try:
                    uuid_contact_id = uuid.UUID(contact_id)
                except ValueError as e:
                    logger.error(f"Invalid contact ID format: {contact_id}, error: {e}")
                    raise ValueError(f"Invalid contact ID format: {contact_id}")
            else:
                uuid_contact_id = contact_id
        
        log = CustomMessageLog(
            contact_id=uuid_contact_id,
            message_content=message_content,
            message_type="sms",
            created_at=datetime.now()
        )
        
        try:
            self.session.add(log)
            self.session.commit()
            self.session.refresh(log)
            return log
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating custom message log: {e}")
            raise
    
    def create_template_message(
        self, 
        name: str, 
        content: str, 
        message_type: str = "sms"
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
    
    def create_scheduled_message(
        self,
        name: str,
        schedule_time: datetime,
        message_type: str = "sms",
        message_id: Optional[Union[uuid.UUID, str]] = None,
        group_id: Optional[Union[uuid.UUID, str]] = None,
        recurring: bool = False,
        recurrence_pattern: Optional[str] = None
    ) -> ScheduledMessage:
        """Create a scheduled message."""
        # Convert string UUIDs to UUID objects if needed
        uuid_message_id = None
        if message_id:
            if isinstance(message_id, str):
                try:
                    uuid_message_id = uuid.UUID(message_id)
                except ValueError as e:
                    logger.error(f"Invalid message ID format: {message_id}, error: {e}")
                    raise ValueError(f"Invalid message ID format: {message_id}")
            else:
                uuid_message_id = message_id
                
        uuid_group_id = None
        if group_id:
            if isinstance(group_id, str):
                try:
                    uuid_group_id = uuid.UUID(group_id)
                except ValueError as e:
                    logger.error(f"Invalid group ID format: {group_id}, error: {e}")
                    raise ValueError(f"Invalid group ID format: {group_id}")
            else:
                uuid_group_id = group_id
        
        scheduled_message = ScheduledMessage(
            name=name,
            message_id=uuid_message_id,
            group_id=uuid_group_id,
            message_type=message_type,
            schedule_time=schedule_time,
            recurring=recurring,
            recurrence_pattern=recurrence_pattern,
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        try:
            self.session.add(scheduled_message)
            self.session.commit()
            self.session.refresh(scheduled_message)
            return scheduled_message
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating scheduled message: {e}")
            raise
    
    def add_contacts_to_scheduled_message(
        self,
        scheduled_message_id: Union[uuid.UUID, str],
        contact_ids: List[Union[uuid.UUID, str]]
    ) -> None:
        """Add contacts to a scheduled message."""
        # Convert scheduled_message_id to UUID if it's a string
        uuid_scheduled_id = scheduled_message_id
        if isinstance(scheduled_message_id, str):
            try:
                uuid_scheduled_id = uuid.UUID(scheduled_message_id)
            except ValueError as e:
                logger.error(f"Invalid scheduled message ID: {scheduled_message_id}, error: {e}")
                raise ValueError(f"Invalid scheduled message ID: {scheduled_message_id}")
                
        # Process each contact ID
        try:
            for contact_id in contact_ids:
                # Convert to UUID if it's a string
                uuid_contact_id = contact_id
                if isinstance(contact_id, str):
                    try:
                        uuid_contact_id = uuid.UUID(contact_id)
                    except ValueError as e:
                        logger.warning(f"Skipping invalid contact ID: {contact_id}, error: {e}")
                        continue
                
                # Create the link
                link = ScheduledMessageContactLink(
                    scheduled_message_id=uuid_scheduled_id,
                    contact_id=uuid_contact_id
                )
                self.session.add(link)
                
            self.session.commit()
            logger.debug(f"Added {len(contact_ids)} contacts to scheduled message {scheduled_message_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding contacts to scheduled message: {e}")
            raise
    
    def get_phone_for_contact(
        self, 
        contact: Contact
    ) -> Tuple[List[PhoneNumber], List[str]]:
        """
        Get prioritized phone numbers for a contact.
        Returns a tuple of (phone_objects, error_messages)
        """
        logger.debug(f"Getting phone numbers for contact: {contact.name} (ID: {contact.id})")
        errors = []
        if not contact.phone_numbers:
            error_msg = f"Contact {contact.name} has no phone numbers"
            errors.append(error_msg)
            logger.debug(error_msg)
            return [], errors
            
        # Sort by priority
        phones = sorted(contact.phone_numbers, key=lambda p: p.priority)
        logger.debug(f"Found {len(phones)} phone numbers for {contact.name}")
        for i, phone in enumerate(phones):
            logger.debug(f"  Phone {i+1}: {phone.number} (priority: {phone.priority})")
        return phones, errors