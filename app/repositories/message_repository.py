"""Message repository for database operations."""
import uuid
from sqlmodel import Session, select
from app.models import Message, SmsLog, CustomMessageLog
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageRepository:
    """Repository for Message database operations."""
    
    def __init__(self, session: Session):
        self.session = session

    def get_message_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """Get a message template by ID."""
        try:
            statement = select(Message).where(Message.id == message_id)
            return self.session.exec(statement).first()
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None

    def get_all_messages(self, active_only: bool = True) -> List[Message]:
        """Get all message templates, optionally filtered by active status."""
        try:
            statement = select(Message)
            if active_only:
                statement = statement.where(Message.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching all messages: {e}")
            return []

    def get_messages_by_type(self, message_type: str, active_only: bool = True) -> List[Message]:
        """Get messages by type (call/sms)."""
        try:
            statement = select(Message).where(Message.message_type == message_type)
            if active_only:
                statement = statement.where(Message.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching messages by type {message_type}: {e}")
            return []

    def search_messages(self, search_term: str, active_only: bool = True) -> List[Message]:
        """Search messages by name or content."""
        try:
            statement = (
                select(Message)
                .where(
                    Message.name.ilike(f"%{search_term}%") |
                    Message.content.ilike(f"%{search_term}%")
                )
            )
            if active_only:
                statement = statement.where(Message.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error searching messages with term '{search_term}': {e}")
            return []

    def create_message(self, message: Message) -> Message:
        """Create a new message template."""
        try:
            self.session.add(message)
            self.session.commit()
            self.session.refresh(message)
            logger.info(f"Created message: {message.name} ({message.id})")
            return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            self.session.rollback()
            raise

    def update_message(self, message: Message) -> Message:
        """Update an existing message template."""
        try:
            self.session.add(message)
            self.session.commit()
            self.session.refresh(message)
            logger.info(f"Updated message: {message.name} ({message.id})")
            return message
        except Exception as e:
            logger.error(f"Error updating message {message.id}: {e}")
            self.session.rollback()
            raise

    def delete_message(self, message_id: uuid.UUID) -> bool:
        """Soft delete a message by setting active=False."""
        try:
            message = self.get_message_by_id(message_id)
            if message:
                message.active = False
                self.session.add(message)
                self.session.commit()
                logger.info(f"Soft deleted message: {message.name} ({message_id})")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            self.session.rollback()
            return False

    # SMS Log operations
    def create_sms_log(self, sms_log: SmsLog) -> SmsLog:
        """Create a new SMS log entry."""
        try:
            self.session.add(sms_log)
            self.session.commit()
            self.session.refresh(sms_log)
            logger.info(f"Created SMS log: {sms_log.id}")
            return sms_log
        except Exception as e:
            logger.error(f"Error creating SMS log: {e}")
            self.session.rollback()
            raise

    def get_sms_logs(self, limit: int = 100, offset: int = 0) -> List[SmsLog]:
        """Get SMS logs with pagination."""
        try:
            statement = (
                select(SmsLog)
                .order_by(SmsLog.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching SMS logs: {e}")
            return []

    def get_sms_logs_by_contact(self, contact_id: uuid.UUID) -> List[SmsLog]:
        """Get SMS logs for a specific contact."""
        try:
            statement = (
                select(SmsLog)
                .where(SmsLog.contact_id == contact_id)
                .order_by(SmsLog.created_at.desc())
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching SMS logs for contact {contact_id}: {e}")
            return []

    # Custom Message Log operations
    def create_custom_message_log(self, custom_log: CustomMessageLog) -> CustomMessageLog:
        """Create a new custom message log entry."""
        try:
            self.session.add(custom_log)
            self.session.commit()
            self.session.refresh(custom_log)
            logger.info(f"Created custom message log: {custom_log.id}")
            return custom_log
        except Exception as e:
            logger.error(f"Error creating custom message log: {e}")
            self.session.rollback()
            raise

    def get_custom_message_logs(self, limit: int = 100, offset: int = 0) -> List[CustomMessageLog]:
        """Get custom message logs with pagination."""
        try:
            statement = (
                select(CustomMessageLog)
                .order_by(CustomMessageLog.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching custom message logs: {e}")
            return []
