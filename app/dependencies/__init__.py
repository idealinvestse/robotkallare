"""Dependency injection and container module."""
from sqlmodel import Session
from app.database import get_session
from app.repositories.call_repository import CallRepository
from app.repositories.sms_repository import SmsRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.outreach_repository import OutreachRepository

from fastapi import Depends

# FastAPI dependency functions for repositories
def get_call_repository(session: Session = Depends(get_session)) -> CallRepository:
    """Get CallRepository instance."""
    return CallRepository(session)

def get_sms_repository(session: Session = Depends(get_session)) -> SmsRepository:
    """Get SmsRepository instance."""
    return SmsRepository(session)

def get_contact_repository(session: Session = Depends(get_session)) -> ContactRepository:
    """Get ContactRepository instance."""
    return ContactRepository(session)

def get_group_repository(session: Session = Depends(get_session)) -> GroupRepository:
    """Get GroupRepository instance."""
    return GroupRepository(session)

def get_message_repository(session: Session = Depends(get_session)) -> MessageRepository:
    """Get MessageRepository instance."""
    return MessageRepository(session)

def get_outreach_repository(session: Session = Depends(get_session)) -> OutreachRepository:
    """Get OutreachRepository instance."""
    return OutreachRepository(session)

# Service dependency functions
def get_outreach_service(session: Session = Depends(get_session)):
    """Get OutreachService instance."""
    from app.services.outreach_service import OutreachService
    return OutreachService(session)

def get_call_service(session: Session = Depends(get_session)):
    """Get CallService instance."""
    from app.services.call_service import CallService
    return CallService(session)

def get_sms_service(session: Session = Depends(get_session)):
    """Get SmsService instance."""
    from app.services.sms_service import SmsService
    return SmsService(session)
