"""Dependency injection for GDial services.

This module provides dependency injection for all services,
following the dependency inversion principle and enabling
easier testing and maintainability.
"""
from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlmodel import Session

from app.database import get_session
from app.services.twilio_call_service import TwilioCallService
from app.services.call_run_service import CallRunService
from app.services.call_orchestration_service import CallOrchestrationService
from app.services.outreach_service import OutreachService
from app.services.sms_service import SmsService
from app.repositories.call_repository import CallRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.outreach_repository import OutreachRepository
from app.repositories.sms_repository import SmsRepository


# Repository Dependencies
def get_call_repository(session: Session = Depends(get_session)) -> CallRepository:
    """Get CallRepository instance."""
    return CallRepository(session)


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


def get_sms_repository(session: Session = Depends(get_session)) -> SmsRepository:
    """Get SmsRepository instance."""
    return SmsRepository(session)


# Service Dependencies
@lru_cache()
def get_twilio_call_service() -> TwilioCallService:
    """Get TwilioCallService singleton instance."""
    return TwilioCallService()


def get_call_run_service(session: Session = Depends(get_session)) -> CallRunService:
    """Get CallRunService instance."""
    return CallRunService(session)


def get_call_orchestration_service(
    session: Session = Depends(get_session),
    twilio_service: TwilioCallService = Depends(get_twilio_call_service),
    call_run_service: CallRunService = Depends(get_call_run_service)
) -> CallOrchestrationService:
    """Get CallOrchestrationService instance with dependencies."""
    return CallOrchestrationService(
        session=session,
        twilio_service=twilio_service,
        call_run_service=call_run_service
    )


def get_outreach_service(
    session: Session = Depends(get_session),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    group_repo: GroupRepository = Depends(get_group_repository),
    outreach_repo: OutreachRepository = Depends(get_outreach_repository),
    call_orchestration_service: CallOrchestrationService = Depends(get_call_orchestration_service)
) -> OutreachService:
    """Get OutreachService instance with dependencies."""
    return OutreachService(
        session=session,
        contact_repo=contact_repo,
        group_repo=group_repo,
        outreach_repo=outreach_repo,
        call_orchestration_service=call_orchestration_service
    )


def get_sms_service(
    session: Session = Depends(get_session),
    sms_repo: SmsRepository = Depends(get_sms_repository)
) -> SmsService:
    """Get SmsService instance with dependencies."""
    return SmsService(session, sms_repo)


# Legacy compatibility - gradually phase out
def get_call_service(session: Session = Depends(get_session)):
    """Legacy CallService dependency - use CallOrchestrationService instead.
    
    This is provided for backward compatibility during the migration.
    New code should use get_call_orchestration_service instead.
    """
    # Import here to avoid circular imports during migration
    from app.services.call_service import CallService
    return CallService(session)
