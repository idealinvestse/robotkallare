"""Group repository for database operations."""
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models import ContactGroup, Contact, ContactGroupMembership
import logging
from typing import List, Optional
import uuid

logger = logging.getLogger(__name__)

class GroupRepository:
    """Repository for ContactGroup database operations."""
    
    def __init__(self, session: Session):
        self.session = session

    def get_group_by_id(self, group_id: uuid.UUID) -> Optional[ContactGroup]:
        """Get a group by ID."""
        try:
            statement = select(ContactGroup).where(ContactGroup.id == group_id)
            return self.session.exec(statement).first()
        except Exception as e:
            logger.error(f"Error fetching group {group_id}: {e}")
            return None

    def get_groups_by_ids(self, group_ids: List[uuid.UUID]) -> List[ContactGroup]:
        """Get multiple groups by IDs."""
        try:
            statement = select(ContactGroup).where(ContactGroup.id.in_(group_ids))
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching groups {group_ids}: {e}")
            return []

    def get_group_by_id_with_contacts(self, group_id: uuid.UUID) -> Optional[ContactGroup]:
        """Get a group by ID with contacts loaded."""
        try:
            statement = (
                select(ContactGroup)
                .options(selectinload(ContactGroup.contacts))
                .where(ContactGroup.id == group_id)
            )
            return self.session.exec(statement).first()
        except Exception as e:
            logger.error(f"Error fetching group with contacts {group_id}: {e}")
            return None

    def get_contacts_by_group_id(self, group_id: uuid.UUID) -> List[Contact]:
        """Get all contacts in a group."""
        try:
            statement = (
                select(Contact)
                .join(ContactGroupMembership)
                .where(ContactGroupMembership.group_id == group_id)
                .where(Contact.active == True)
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching contacts for group {group_id}: {e}")
            return []

    def get_all_groups(self, active_only: bool = True) -> List[ContactGroup]:
        """Get all groups, optionally filtered by active status."""
        try:
            statement = select(ContactGroup)
            if active_only:
                statement = statement.where(ContactGroup.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching all groups: {e}")
            return []

    def search_groups(self, search_term: str, active_only: bool = True) -> List[ContactGroup]:
        """Search groups by name or description."""
        try:
            statement = (
                select(ContactGroup)
                .where(
                    ContactGroup.name.ilike(f"%{search_term}%")
                )
            )
            if active_only:
                statement = statement.where(ContactGroup.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error searching groups with term '{search_term}': {e}")
            return []

    def create_group(self, group: ContactGroup) -> ContactGroup:
        """Create a new group."""
        try:
            self.session.add(group)
            self.session.commit()
            self.session.refresh(group)
            logger.info(f"Created group: {group.name} ({group.id})")
            return group
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            self.session.rollback()
            raise

    def update_group(self, group: ContactGroup) -> ContactGroup:
        """Update an existing group."""
        try:
            self.session.add(group)
            self.session.commit()
            self.session.refresh(group)
            logger.info(f"Updated group: {group.name} ({group.id})")
            return group
        except Exception as e:
            logger.error(f"Error updating group {group.id}: {e}")
            self.session.rollback()
            raise

    def delete_group(self, group_id: uuid.UUID) -> bool:
        """Soft delete a group by setting active=False."""
        try:
            group = self.get_group_by_id(group_id)
            if group:
                group.active = False
                self.session.add(group)
                self.session.commit()
                logger.info(f"Soft deleted group: {group.name} ({group_id})")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {e}")
            self.session.rollback()
            return False

    def add_contact_to_group(self, group_id: uuid.UUID, contact_id: uuid.UUID) -> bool:
        """Add a contact to a group."""
        try:
            # Check if membership already exists
            existing = self.session.exec(
                select(ContactGroupMembership)
                .where(ContactGroupMembership.group_id == group_id)
                .where(ContactGroupMembership.contact_id == contact_id)
            ).first()
            
            if existing:
                logger.info(f"Contact {contact_id} already in group {group_id}")
                return True
            
            membership = ContactGroupMembership(
                group_id=group_id,
                contact_id=contact_id
            )
            self.session.add(membership)
            self.session.commit()
            logger.info(f"Added contact {contact_id} to group {group_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding contact {contact_id} to group {group_id}: {e}")
            self.session.rollback()
            return False

    def remove_contact_from_group(self, group_id: uuid.UUID, contact_id: uuid.UUID) -> bool:
        """Remove a contact from a group."""
        try:
            membership = self.session.exec(
                select(ContactGroupMembership)
                .where(ContactGroupMembership.group_id == group_id)
                .where(ContactGroupMembership.contact_id == contact_id)
            ).first()
            
            if membership:
                self.session.delete(membership)
                self.session.commit()
                logger.info(f"Removed contact {contact_id} from group {group_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing contact {contact_id} from group {group_id}: {e}")
            self.session.rollback()
            return False
