"""Contact repository for database operations."""
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models import Contact, PhoneNumber
import logging
from typing import List, Optional
import uuid

logger = logging.getLogger(__name__)

class ContactRepository:
    """Repository for Contact database operations."""
    
    def __init__(self, session: Session):
        self.session = session

    def get_contact_by_id(self, contact_id: uuid.UUID) -> Optional[Contact]:
        """Get a contact by ID with phone numbers loaded."""
        try:
            statement = (
                select(Contact)
                .options(selectinload(Contact.phone_numbers))
                .where(Contact.id == contact_id)
            )
            return self.session.exec(statement).first()
        except Exception as e:
            logger.error(f"Error fetching contact {contact_id}: {e}")
            return None

    def get_contacts_by_ids(self, contact_ids: List[uuid.UUID]) -> List[Contact]:
        """Get multiple contacts by IDs with phone numbers loaded."""
        try:
            statement = (
                select(Contact)
                .options(selectinload(Contact.phone_numbers))
                .where(Contact.id.in_(contact_ids))
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching contacts {contact_ids}: {e}")
            return []

    def get_all_contacts(self, active_only: bool = True) -> List[Contact]:
        """Get all contacts, optionally filtered by active status."""
        try:
            statement = (
                select(Contact)
                .options(selectinload(Contact.phone_numbers))
            )
            if active_only:
                statement = statement.where(Contact.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching all contacts: {e}")
            return []

    def search_contacts(self, search_term: str, active_only: bool = True) -> List[Contact]:
        """Search contacts by name or phone number."""
        try:
            statement = (
                select(Contact)
                .options(selectinload(Contact.phone_numbers))
                .where(
                    Contact.name.ilike(f"%{search_term}%")
                )
            )
            if active_only:
                statement = statement.where(Contact.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error searching contacts with term '{search_term}': {e}")
            return []

    def create_contact(self, contact: Contact) -> Contact:
        """Create a new contact."""
        try:
            self.session.add(contact)
            self.session.commit()
            self.session.refresh(contact)
            logger.info(f"Created contact: {contact.name} ({contact.id})")
            return contact
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            self.session.rollback()
            raise

    def update_contact(self, contact: Contact) -> Contact:
        """Update an existing contact."""
        try:
            self.session.add(contact)
            self.session.commit()
            self.session.refresh(contact)
            logger.info(f"Updated contact: {contact.name} ({contact.id})")
            return contact
        except Exception as e:
            logger.error(f"Error updating contact {contact.id}: {e}")
            self.session.rollback()
            raise

    def delete_contact(self, contact_id: uuid.UUID) -> bool:
        """Soft delete a contact by setting active=False."""
        try:
            contact = self.get_contact_by_id(contact_id)
            if contact:
                contact.active = False
                self.session.add(contact)
                self.session.commit()
                logger.info(f"Soft deleted contact: {contact.name} ({contact_id})")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id}: {e}")
            self.session.rollback()
            return False

    def get_contacts_with_phone_numbers(self) -> List[Contact]:
        """Get all active contacts that have phone numbers."""
        try:
            statement = (
                select(Contact)
                .options(selectinload(Contact.phone_numbers))
                .join(PhoneNumber)
                .where(Contact.active == True)
                .distinct()
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching contacts with phone numbers: {e}")
            return []
