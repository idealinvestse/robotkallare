"""
UUID compatibility fix for SmsRepository.

This module provides a patched version of the SmsRepository.get_message_by_id method
that correctly handles UUID conversion and database queries.
"""

import uuid
import sqlite3
import logging
from typing import Optional

from app.models import Message
from app.config import get_settings
from app.repositories.sms_repository import SmsRepository

logger = logging.getLogger(__name__)

def fix_message_by_id_method() -> None:
    """
    Applies a fix to the SmsRepository.get_message_by_id method to handle UUID conversion
    and database queries properly.
    """
    # Store the original method for reference
    original_method = SmsRepository.get_message_by_id
    
    def patched_get_message_by_id(self, message_id):
        """
        Patched version of get_message_by_id that handles UUIDs correctly.
        
        Uses direct SQLite queries as a fallback when the ORM query fails due to
        UUID conversion issues.
        
        Args:
            message_id: The message ID as UUID or string
            
        Returns:
            Message: The message object if found, None otherwise
        """
        logger.debug(f"Patched get_message_by_id called with ID: {message_id}")
        
        # First try the ORM approach (may fail with certain UUID formats)
        try:
            # Convert string to UUID if needed
            uuid_obj = message_id
            if isinstance(message_id, str):
                try:
                    uuid_obj = uuid.UUID(message_id)
                except ValueError:
                    pass  # Will try direct query next
                    
            # Only try ORM if we have a valid UUID object
            if isinstance(uuid_obj, uuid.UUID):
                # Try the original method
                message = original_method(self, uuid_obj)
                if message:
                    return message
        except Exception as e:
            logger.error(f"Error in ORM query: {e}")
        
        # Fallback to direct SQLite query
        return direct_db_get_message(message_id, self.session)

    def direct_db_get_message(message_id, session):
        """
        Query the message directly from SQLite database.
        
        Args:
            message_id: The message ID as string or UUID
            session: The SQLModel session (used for its connection)
            
        Returns:
            Message: The message object if found, None otherwise
        """
        # Convert to string if it's a UUID object
        if isinstance(message_id, uuid.UUID):
            message_id = str(message_id)
            
        # Get database path
        db_path = get_settings().SQLITE_DB.replace("sqlite:///", "")
        
        try:
            # Connect directly to SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to find with exact ID match
            cursor.execute(
                "SELECT id, name, content, is_template, message_type, created_at, updated_at "
                "FROM message WHERE id = ?", 
                (message_id,)
            )
            row = cursor.fetchone()
            
            # If not found and ID has hyphens, try without hyphens
            if not row and '-' in message_id:
                no_hyphens = message_id.replace('-', '')
                cursor.execute(
                    "SELECT id, name, content, is_template, message_type, created_at, updated_at "
                    "FROM message WHERE id = ?", 
                    (no_hyphens,)
                )
                row = cursor.fetchone()
                
            conn.close()
            
            # Create Message object from row
            if row:
                logger.debug(f"Found message via direct query: {row[1]}")
                message = Message(
                    id=row[0],
                    name=row[1],
                    content=row[2],
                    is_template=bool(row[3]),
                    message_type=row[4],
                    created_at=row[5] if row[5] else None,
                    updated_at=row[6] if row[6] else None
                )
                return message
                
            logger.debug(f"No message found with ID: {message_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error in direct database query: {e}")
            return None
    
    # Apply the patch
    SmsRepository.get_message_by_id = patched_get_message_by_id
    logger.info("Applied patch to SmsRepository.get_message_by_id")